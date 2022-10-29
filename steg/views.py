from email.mime import image
from django.http import FileResponse, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from sinimg.forms import SinImgForm
from sinimg.models import SinImg
from django.contrib import messages
from django.http import HttpResponseRedirect
import cv2
import numpy as np
import urllib.request

from steg.functions import hide_lsb, reveal_lsb, hide_lsbset, reveal_lsbset

CHOICES = ["LSB Hide", "LSB Reveal", "LSB Set Hide", "LSB Set Reveal"]

def get_image(obj):
# Retrieving the image and storing it in memory
    url = obj.img.url
    req = urllib.request.urlopen(url)
    arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
    path = cv2.imdecode(arr, -1) # 'Load it as it is'
    return path

class ProcessImage(View):
    def get(self, request, choice):
        # messages.success(request, "Updated successfully!")
        return render(request, "steg/process.html")

    def post(self, request, choice):
        option = request.POST.get("type")

        id = request.session.get("id")
        obj = SinImg.objects.get(id=id)
        
        path = get_image(obj)
        sec_msg = request.session.get("message", None)

        content_type = "image/png"
        file_name = "demo.png"
        

        if choice == 0:
            img = hide_lsb(path, sec_msg)
        elif choice == 2:
            img = hide_lsbset(path, sec_msg)
        else:
            return HttpResponse("Invalid Option")

        if option == "Preview":
            image_data = img.getvalue()
            return HttpResponse(image_data, content_type=content_type)
        elif option == "Download":
            return FileResponse(img, as_attachment=True, filename=file_name)
        else:
            return HttpResponse("Invalid Option")

class SelectChoice(View):

    def get(self, request):

        id = request.session.get("id")
        obj = SinImg.objects.get(id=id)

        context={
                "object": obj, 
                "choices": CHOICES,
                }

        return render(request, "steg/select_choice.html", context)

    def post(self, request):

        type = request.POST.get("type")
        request.session["message"] = request.POST.get("message", None)

        id = request.session.get("id")
        obj = SinImg.objects.get(id=id)

        if type:    
            choice_id = CHOICES.index(type)
            if choice_id in [1, 3]:
                path = get_image(obj)
                if choice_id == 1:
                    msg, img = reveal_lsb(path)
                elif choice_id == 3:
                    msg, img = reveal_lsbset(path)
                return render(request, "steg/show_message.html", {"msg": msg})

            return redirect((reverse_lazy("steg:process", kwargs={"choice": choice_id})))
        else:
            return HttpResponse("Invalid Choice")

class Upload(View):

    def get(self, request):
        form = SinImgForm()
        context = {
            "form": form,
        }
        return render(request, "steg/upload.html", context)
    
    def post(self, request):
        form = SinImgForm(request.POST, request.FILES)

        if form.is_valid():
            obj = form.save()
            request.session['id'] = obj.id     

            return redirect(reverse_lazy("steg:select-choice"))
        else:
            messages.warning(request, 'Please select a Picture')
            return HttpResponseRedirect(request.path)