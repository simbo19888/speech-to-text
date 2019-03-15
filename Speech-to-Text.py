#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

import time
import wave
import requests

try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    print("""
    Importing the Speech SDK for Python failed.
    Refer to
    https://docs.microsoft.com/azure/cognitive-services/speech-service/quickstart-python for
    installation instructions.
    """)
    import sys
    sys.exit(1)


# Set up the subscription info for the Speech Service:
# Replace with your own subscription key and service region (e.g., "westus").
speech_key, service_region = "YOUR_SPEECH_KEY", "westus" 
fromLanguage = "ru-RU"
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_recognition_language = fromLanguage

# Specify the path to an audio file containing speech (mono WAV / PCM with a sampling rate of 16
# kHz).

def speech_recognize_once_from_mic():
    """performs one-shot speech recognition from the default microphone"""
    # <SpeechRecognitionWithMicrophone>
    # Creates a speech recognizer using microphone as audio input.
    # The default language is "en-us".
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

    # Starts speech recognition, and returns after a single utterance is recognized. The end of a
    # single utterance is determined by listening for silence at the end or until a maximum of 15
    # seconds of audio is processed. It returns the recognition text as result.
    # Note: Since recognize_once() returns only a single utterance, it is suitable only for single
    # shot recognition like command or query.
    # For long-running multi-utterance recognition, use start_continuous_recognition() instead.
    result = speech_recognizer.recognize_once()

    f = open('text.txt', 'w')
    
    # Check the result
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        f.write(result.text)
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
    # </SpeechRecognitionWithMicrophone>


def speech_recognize_once_from_file(filename):
    """performs one-shot speech recognition with input from an audio file"""
    # <SpeechRecognitionWithFile>
    audio_config = speechsdk.audio.AudioConfig(filename=filename)
    # Creates a speech recognizer using a file as audio input.
    # The default language is "en-us".
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    # Starts speech recognition, and returns after a single utterance is recognized. The end of a
    # single utterance is determined by listening for silence at the end or until a maximum of 15
    # seconds of audio is processed. It returns the recognition text as result.
    # Note: Since recognize_once() returns only a single utterance, it is suitable only for single
    # shot recognition like command or query.
    # For long-running multi-utterance recognition, use start_continuous_recognition() instead.
    result = speech_recognizer.recognize_once()

    f = open('text.txt', 'w')
    
    # Check the result
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        f.write(result.text)
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(result.no_match_details))
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
    # </SpeechRecognitionWithFile>


def speech_recognize_continuous_from_file(filename):
    """performs continuous speech recognition with input from an audio file"""
    # <SpeechContinuousRecognitionWithFile>
    audio_config = speechsdk.audio.AudioConfig(filename=filename)

    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    done = False

    def stop_cb(evt):
        """callback that stops continuous recognition upon receiving an event `evt`"""
        print('OK')
        speech_recognizer.stop_continuous_recognition()
        nonlocal done
        done = True
        
        
    f = open('text.txt', 'w')
    def add_result(evt):
        f.write(evt.result.text+'\n')
    
    #def print_result():
     #   nonlocal result
     #   print(result)
        
     
    # Connect callbacks to the events fired by the speech recognizer
    #speech_recognizer.recognizing.connect(lambda evt: print('RECOGNIZING: {}'.format(evt))) #Вывод промежуточных результатов
    speech_recognizer.recognized.connect(add_result)
    speech_recognizer.session_started.connect(lambda evt: print('processing...'))
    speech_recognizer.session_stopped.connect(stop_cb)

    # Start continuous speech recognition
    speech_recognizer.start_continuous_recognition()
    while not done:
        time.sleep(.5)
    f.close()
    # </SpeechContinuousRecognitionWithFile>




def speech_recognition_with_push_stream(stream_url):
    """gives an example how to use a push audio stream to recognize speech from a custom audio
    source"""
    
    
    # setup the audio stream
    stream = speechsdk.audio.PushAudioInputStream()
    audio_config = speechsdk.audio.AudioConfig(stream=stream)

    # instantiate the speech recognizer with push stream input
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    f = open('text.txt', 'w')
    
    def stop_cb(evt):
        #"""callback that stops continuous recognition upon receiving an event evt"""
        speech_recognizer.stop_continuous_recognition()
        f.close()
    
    
    def add_result(evt):
        f.write(evt.result.text)
    
    
    # Connect callbacks to the events fired by the speech recognizer
    
    #speech_recognizer.recognizing.connect(lambda evt: print('RECOGNIZING: {}'.format(evt))) #Вывод промежуточных результатов
    speech_recognizer.recognized.connect(add_result)
    speech_recognizer.session_started.connect(lambda evt: print('processing...'))
    speech_recognizer.session_stopped.connect(stop_cb)

    # The number of bytes to push per buffer
    n_bytes = 3200

    # start continuous speech recognition
    speech_recognizer.start_continuous_recognition_async()
    
    r = requests.get(stream_url, stream = True)

    # start pushing data
    try:
        for block in r.iter_content(n_bytes):
            #print('read {} bytes'.format(len(block)))
            if not block:
                break

            stream.write(block)
            time.sleep(.1)
    finally:
        stream.close()
        r.close()
    

while(True):
    a = int(input(fromLanguage+'''
                 1 - file < 15sec
                 2 - file
                 3 - stream
                 4 - mic
                 5 - en lang
                 6 - ru lang
                 other - break
                 '''))
    if (a == 1):
        speech_recognize_once_from_file(input('file path: '))
    elif (a == 2):
        speech_recognize_continuous_from_file(input('file path: '))
    elif (a == 3):
        speech_recognition_with_push_stream(input('stream url: '))
    elif (a == 4):
        speech_recognize_once_from_mic()
    elif (a == 5):
        fromLanguage = "en-US"
        speech_config.speech_recognition_language = fromLanguage
    elif (a == 6):
        fromLanguage = "ru-RU"
        speech_config.speech_recognition_language = fromLanguage
    else:
        break
