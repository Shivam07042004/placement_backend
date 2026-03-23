from django.shortcuts import render
from .models import Job
from .serializers import JobSerializer, LoginSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token


# Create your views here.
class JobList(APIView):

    def get(self,request):
        jobs = Job.objects.all()
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self,request):
        serializer = JobSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)


class JobDetail(APIView):

    def get_object(self,pk):
        try:
            job = Job.objects.get(pk=pk)
            return job
        except Job.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    
    def get(self,request,pk):
        job = self.get_object(pk)
        serializer = JobSerializer(job)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def put(self,request,pk):
        job = self.get_object(pk)
        serializer = JobSerializer(job,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status = status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self,request,pk):
        job = self.get_object(pk)
        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LoginAPI(APIView):
    def post(self, request):
        serializer = LoginSerializer(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user_obj = authenticate(username=username, password=password)

        if user_obj:
            token, created = Token.objects.get_or_create(user=user_obj)
            return Response({"message": "Login successful", "token": token.key}, status=status.HTTP_200_OK)
        
        return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

