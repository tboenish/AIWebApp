#from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import json
from pytube import YouTube
import os
import assemblyai as aai
import openai

# Create your views here.
@login_required

def home(request):
    return render(request, 'home.html')

@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            yt_link = data['link']
            #return JsonResponse({'content': yt_link})
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid Data Sent'}, status = 400)
        
        #get title
        title = yt_title(yt_link)

        #get transcript
        transcription = get_transcription(yt_link)
        if not transcription:
            return JsonResponse({'error': "Failed to get transcript"}, status=500)


        #use OpenAI to generate the blog

        blog_content = generate_blog_from_transcription(transcription)
        if not blog_content:
            return JsonResponse({'error': "Failed to generate blog article"}, status=500)


        #save article to database

        #return the article as the response
        return JsonResponse({'content':blog_content})


    else:
        return JsonResponse({'error': 'Invalid Request Method'}, status = 405)

def yt_title(link):
    yt = YouTube(link)
    title = yt.title
    return title

def download_audio(link):
    yt = YouTube(link)
    video = yt.streams.filter(only_audio=True).first()
    out_file= video.download(output_path=settings.MEDIA_ROOT)
    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    os.rename(out_file,new_file)
    return new_file

def get_transcription(link):
    audio_file = download_audio(link)
    aai.settings.api_key="e277a7f9ee36471da0a6d86c41fbc806"

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)

    return transcript.text

def generate_blog_from_transcription(transcription):
    openai.api_key="sk-proj-ITo8OeOYe4IDJeaHXbRbT3BlbkFJKSA9tPkG3wP0i8UDWg4t"

    prompt = f"Based on the given YouTube Video transcript, write a complete and comprehensive summary based on the transcript. Do not make it sound like a YouTube Video, make it read like a real description:\n\n{transcription}\n\nArticle:"

    response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=1000
    )

    generated_content = response.choices[0].text.strip()

    return generated_content




def user_login(request):

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST ['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error_message="Invalid Username or Password"
            return render(request,'login.html', {'error_message': error_message})

    return render(request,'login.html')

def user_signup(request):
    if request.method == 'POST':

        username = request.POST['username']
        email = request.POST['email']
        password = request.POST ['password']
        repeatPassword = request.POST ['repeatPassword']

        if password == repeatPassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except:
                error_message = 'Error Creating Account'
                return render(request, 'signup.html', {'error_message':error_message})
        else:
            error_message = 'Passwords Do Not Match'
            return render(request, 'signup.html', {'error_message':error_message})

    return render(request, 'signup.html')

def user_logout(request):
    logout(request)
    return redirect('/')