from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import HttpResponse
from django.core import mail
from django.core.mail import send_mail
import json
from django.db import connection    # allow Django to use the original SQL statements
from datetime import date, datetime
import os
import random
import _thread
import time
import queue
from sphere_engine import CompilersClientV4
from sphere_engine.exceptions import SphereEngineException
import requests
import urllib.request
import pymysql

from .models import User
from .models import Blog_Questions
from .models import picture
from .models import Blog_Answers
from .models import user_like_question
from .models import user_follow_question
from .models import user_follow_group
from .models import user_like_answer
from .models import Group
from .models import sub_group
from .models import file
import hashlib
import markdown
import spacy

from . import Unit_Test
from . import Component_Test
from . import System_Test

# 重写python的datetime类型
class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)


#校验登陆状态：装饰器。
def check_state(fn):# fn is the views
    def wrap(request, *args, **kwargs): #parameters of views
        if 'username' not in request.session or 'uid' not in request.session:
            c_username = request.COOKIES.get('username')
            c_uid = request.COOKIES.get('uid')
            if not c_username or not c_uid:
                return HttpResponseRedirect('/index')
            else:
                #write back
                request.session['username'] = c_username
                request.session['uid'] = c_uid
        return fn(request, *args, **kwargs)
    return wrap

#生成密码
def encode(n = 6):
    all_code = '012345678mchjsmejrigebriruwioihgdvbhserjebssse9P'
    index = len(all_code)
    code = ''
    for  i in range(n):
        num = random.randint(0,index-1)
        code += all_code[num]
    return code

##############################
# Create your views here.
def index(request):  # request means the request sent by front-end
    if request.method == 'GET':  #GET 返回页面
        return render(request, 'index.html')

# def register(request):
#     #POST 处理数据
#         #1.当前用户名是否可用
#         #1.插入数据[暂时明文处理]
#     data = {
#         'isRegister': 1
#     }# control flag

#     if request.method == 'POST':
#         username = request.POST['username']
#         email = request.POST['email']
#         password = request.POST['password']
#         print(username,email,password)

#         #check user name. Multi-thread considerration.
#         old_users = User.objects.filter(username=username)
#         print(old_users)
#         if (old_users):# if exists
#             data['isRegister'] = 0
#             return HttpResponse(json.dumps(data), content_type='application/json')
        
#         ##hash the code
#         m = hashlib.md5()
#         m.update(password.encode())
#         password_m = m.hexdigest()
        
#         try: #Multi-thread considerration:唯一索引，并发写入问题。
#         #insert data
#             user = User.objects.create(username=username, password=password_m, email=email)
#         except Exception as e:
#             print('--create user error%s'%(e))
#             data['isRegister'] = 0
#             return HttpResponse(json.dumps(data), content_type='application/json')


#         #免登录一天 session
#         request.session['username'] = username
#         request.session['uid'] = user.id
#         #TODO 修改session储存时间为一天

#         #return successful information
#         return HttpResponse(json.dumps(data), content_type='application/json')

def register(request):
    #POST 处理数据
        #1.当前用户名是否可用
        #1.插入数据[暂时明文处理]
    data = {
        'isRegister': 1
    }# control flag

    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        #check user name. Multi-thread considerration.
        old_users = User.objects.filter(username=username)
        if (old_users):# if exists
            data['isRegister'] = 0
            return HttpResponse(json.dumps(data), content_type='application/json')

        #return successful information
        return HttpResponse(json.dumps(data), content_type='application/json')
    else:
        data['isRegister'] = 0
        return HttpResponse(json.dumps(data), content_type='application/json')

def verify(request):
    data = {
        'isRegister': 1
    }# control flag
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        ##hash the code
        m = hashlib.md5()
        m.update(password.encode())
        password_m = m.hexdigest()
        
        try: #Multi-thread consideration:唯一索引，并发写入问题。
        #insert data
            user = User.objects.create(username=username, password=password_m, email=email)
        except Exception as e:
            print('--create user error%s'%(e))
            data['isRegister'] = 0
            return HttpResponse(json.dumps(data), content_type='application/json')
        
        #免登录一天 session
        request.session['username'] = username
        request.session['uid'] = user.id
        #TODO 修改session储存时间为一天

        return HttpResponse(json.dumps(data), content_type='application/json')



def login(request):
    if request.method == 'GET':
        ##1.检查会话状态session
        if request.session.get('username') and request.session.get('uid'):
            return HttpResponseRedirect('/login/#/home/hands')
        ##2.检查会话状态cookies
        c_username = request.COOKIES.get('username')
        c_uid = request.COOKIES.get('uid')
        if c_username and c_uid:
            #回写cookies
            request.session['username'] = username
            request.session['uid'] = user.id
            return HttpResponseRedirect('/login/#/home/hands')
        ##3. 未登陆过，则登录
        return render(request, 'index.html')
    
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        try:  #get the user infor.
            user = User.objects.get(username=username)
        except Exception as e:
            print('---login user error %s'%(e))
            return HttpResponse('Username or Password Error. Please check!')

        #compare the passsword
        m = hashlib.md5()
        m.update(password.encode())
        if m.hexdigest() != user.password:
            return HttpResponse("Username or Password Error. Please check!")

        #remember seesion,记录会话状态
        request.session['username'] = username
        request.session['uid'] = user.id
        resp = HttpResponse('Success Login!')
        #remember or not -> coockie
        if 'remember' in request.POST:
            resp.set_cookie('username', username, 3600*24*3)
            resp.set_cookie('uid', user.id, 3600*24*3)

        return resp


def logout(request):
    #delete
    if 'username' in request.session:
        del request.session['username']
    if 'uid' in request.session:
        del request.session['uid']
    
    resp = HttpResponseRedirect('/index')
    if 'username' in request.COOKIES:
        resp.delete_cookie('username')
    if 'uid' in request.COOKIES:
        resp.delete_cookie('uid')
    return resp


@check_state
def after_login(request):
    return render(request, 'after_index.html')


def update(request):
    
    data = {    #api detail.
        'isRegister': 1
    }# control flag

    if request.method == 'POST':
        _type = request.POST['type']
        newVal = request.POST['newVal']
        oldName = request.POST['username']

        if _type == 'Reset Username':
            #更新用户名
            old_users = User.objects.filter(username=newVal)
            if (old_users):# if exists
                data['isRegister'] = 0  #need to adjust
                return HttpResponse('UserName has been taken')
            else:   #valid username
                user = User.objects.get(username=oldName)
                user.username = newVal
                user.save()
                return HttpResponse('UserName Reset successfully!')
        
        elif _type == 'Reset Password':
            #更新密码
            ##hash the code
            m = hashlib.md5()
            m.update(newVal.encode())
            password_m = m.hexdigest()

            user = User.objects.get(username=oldName)
            user.password = password_m
            user.save()
            return HttpResponse('Password Reset successfully!')
    return HttpResponse('Password Reset failed!')



#not yet
def sendEmail(request):
    #send email heres
    #is href a POST or a GET request?
    if request.method == 'POST':
        try: 
            email = request.POST['email']
        except:        # if it is a WSGIRequest, it don't have .POST[""] method, so we have to retrieve it by ourselves
            email = request.META["QUERY_STRING"]
            for i in range(0, len(email)):
                if (email[i] == "="):
                    email = email[i+1:]
                    break
        code_send = encode()
        if (email[9:] != "@link.cuhk.edu.cn"):
            return HttpResponse('Invalid email address!')


        R_list = []
        R_list.append(email)
        mail.send_mail(subject='Register code', message=code_send, from_email='1092298689@qq.com', recipient_list=R_list)

        data = {}
        data["code"] = code_send
        
        return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json')#需要把信息验证码一起用字典传过去、或者设置全局变量。

# def setQuestion(request):
#     data = {
#         'isRegister': 1
#     }# control flag

#     if request.method == 'POST':
#         title = request.POST['title']
#         author_id = request.POST['author_id']
#         group_type = request.POST['group_type']
#         sub_group_type = request.POST['sub_group_type']
#         content = request.POST['content']
#         content_format = request.POST['content_format']
#         like = request.POST['like']
#         follow = request.POST['follow']
#         hot = request.POST['hot']
#         views = request.POST['views']

#         try: 
#         #insert data
#             user = Blog_Questions.objects.create(title=title, author_id=author_id, group_type=group_type, sub_group_type=sub_group_type, \
#                                                 content=content, content_format=content_format, like=like, follow=follow, hot=hot, views=views)
#         except Exception as e:
#             print('--Insert question error%s'%(e))
#             data['isRegister'] = 0
#             return HttpResponse(json.dumps(data), content_type='application/json')

#         #if success
#         return HttpResponse(json.dumps(data), content_type='application/json')

#提出问题并放入数据库
#需要对接如何返回
def setQuestion(request):
    data = {
        'ok': 0
    }# control flag

    if request.method == 'POST':

        try:
            title = request.POST['title']
        except:
            return HttpResponse('Receive no tile!')

        try:
            author_name = request.POST['author_name']
            author_id = User.objects.filter(username = author_name).values()[0]['id']
        except:
            return HttpResponse('No Such Username!')

        try:
            group_type = request.POST['group_type']
            sub_group_type_name = request.POST['sub_group_type']
            sub_group_type = sub_group.objects.filter(sub_group_name = sub_group_type_name, group_name = group_type).values()[0]['id']
        except:
            return HttpResponse(json.dumps(data), content_type='application/json')
        
        try:
            content = request.POST['content']
        except:
            return HttpResponse('Receive empty content!')
        content_format = "HTML"

        try:
          StringText =  request.POST['StringText']
        except:
          return HttpResponse('Receive empty stringtext!')

        fs_url = ""
        pics_url = ""
        try:
            fs_url = request.POST['files_url']
        except:
            pass

        try:
            code = request.POST['code']
            lang = request.POST['lang']
        except:
            code = ""
            land = ""


        like = 0
        follow = 0
        hot = 0
        views = 0

        # try: 
        #insert data
        new_question = Blog_Questions.objects.create(title=title, author_id=author_id, group_type=group_type, sub_group_type=sub_group_type, \
                                            content=content, content_format=content_format, like=like, follow=follow, hot=hot, views=views, \
                                            code = code, lang = lang)
       
        new_q_id = new_question.id
        print(StringText[len(StringText)-24:])
        if (StringText[len(StringText)-24:] == "Powered by Froala Editor"):
          StringText = StringText[0:len(StringText)-24]
        print(StringText)
        index_list = filter_word([new_q_id, title, StringText]) # id, dict_title, dict_content
        
        print(index_list)

        conn = pymysql.connect(host="175.178.34.84", port=3306, user="root", passwd="Q@@pr294118", db="CSC3170", charset="utf8")
        cursor = conn.cursor()
        for item in index_list:
            mydata = []
            mydata.append(item)
            if item[0][0].isalpha():
                sql = 'insert into Our_project_{} values(%s,%s,%s,%s);'.format(item[0][0].upper())
                res = cursor.executemany(sql, mydata)
                conn.commit()
                print("ordinary insert done")
            else:
                sql = 'insert into Our_project_{} values(%s,%s,%s,%s);'.format('OTHERS')
                res = cursor.executemany(sql, mydata)
                conn.commit()
                print("insert into others done")
        cursor.close()
        conn.close()
        # store the files url and pics url

        for i in range(0, len(fs_url)):
            if fs_url[i] == ".":
                extension = fs_url[i:]
                print(extension)
        if (fs_url != ""):
            if (extension == ".jpg" or extension == ".png" or extension == ".JPG" or extension == ".PNG" or extension == ".GIF" or extension == ".gif" or extension == ".JPEG" or extension == ".jpeg"):
                pic = picture.objects.create(url = fs_url, question = new_q_id, group_name = None)
            else:
                fs = file.objects.create(url = fs_url, corresponding_question = new_q_id)
        data['ok'] = 1

        return HttpResponse(json.dumps(data), content_type='application/json')
    else:
        return HttpResponse('Please use POST request!')

#基于title相似度写的问题搜索
def searchQuestion(request):
    if request.method == 'GET':
        return render(request, 'search.html') ##需修改html
    
    if request.method == 'POST':
        similarity = 0
        answerList = []
        #get the infor
        question1 = request.POST['content'] #question in test
        # question = question.upper()
        # questionElem = question.split(' ')
        question2 = search_spilt(question1)
        dim = question2[0]
        question = question2[1]
        target_vec = question2[2]

        scope = request.POST['scope']

        username = request.POST['username']
        userid = User.objects.filter(username = username).values()[0]['id']
        

        if (scope=='All'):
            conn = pymysql.connect(host="175.178.34.84", port=3306, user="root", passwd="Q@@pr294118", db="CSC3170", charset="utf8")
            cursor = conn.cursor()
            Answer_T = []
            Answer_C = []
            blockNumberTotalList = []
            lenList = len(question)
            searchIndex = 1
            for item in question:
                if item[0].isalpha:
                    sql = 'select * from Our_project_{} where WORDS = "{}";'.format(item[0].upper(), item)
                    cursor.execute(sql)
                    a=cursor.fetchall()
                    # print(a)
                    # print(len(a))
                else:  
                    sql = 'select * from Our_project_{} where WORDS = "{}";'.format('OTHERS', item)
                    cursor.execute(sql)
                    a=cursor.fetchall()
                
                for i in range(len(a)):
                    if a[i][1] not in blockNumberTotalList: blockNumberTotalList.append(a[i][1])
                    Ttemp1 = [0]*(lenList+1)
                    Ctemp1 = [0]*(lenList+1)
                    Ttemp1[0] = a[i][1]
                    Ttemp1[searchIndex] = a[i][2]
                    Ctemp1[0] = a[i][1]
                    Ctemp1[searchIndex] = a[i][3]
                    Answer_T.append(Ttemp1)
                    Answer_C.append(Ctemp1)
                searchIndex += 1
            searchIndex -= 1
            # print(blockNumberTotalList)
            print(Answer_T)
            print(Answer_C)
              

            finalT = {}
            finalC = {}
            for item in blockNumberTotalList:
                temp1 = [0]*(lenList)
                temp2 = [0]*(lenList)
                finalT[item] = temp1
                finalC[item] = temp2

            # print(finalT)
            # print(finalC,"nima")
            for item in Answer_T:
                blocknumber = item[0]
                for i in range(1,lenList+1):
                    if item[i] != 0:
                        finalT[blocknumber][i-1] = item[i]

          
            for item in Answer_C:
                blocknumber = item[0]
                for i in range(1,lenList+1):
                    if item[i] != 0:
                        finalC[blocknumber][i-1] = item[i]
            print(finalT)
            print(finalC)# content
          
            blog_vec_list = []
            my_dict = {} . 
            for (key,value) in finalT.items():
              blog_id = key
              title_value = value
              content_value = finalC[key]
              vec = []
              vec.append(blog_id)
              for j in range(0, len(title_value)):
                myvalue = 3 * title_value[j] + content_value[j]
                vec.append(myvalue)
              blog_vec_list.append(vec)

            print(blog_vec_list)
            result_list = quicksort_blog(dim,target_vec,blog_vec_list,0,len(blog_vec_list)-1)
            print(result_list)





            #finially, return the searched answer
            ALL_blogs = Blog_Questions.objects.values()
            data = {}
            for i in range(len(positionList)):
                temp = ALL_blogs[positionList[i]]
                rawContent = temp['content']
                answerID = temp['id']
                amount_of_answers = Blog_Answers.objects.filter(question_id = answerID).count()
                temp['amount_of_answers'] = amount_of_answers
                isliked = 0
                if (user_like_question.objects.filter(question_id = answerID, id = userid)): isliked = 1
                temp['isliked'] = isliked

                isfollowed = 0
                if (user_follow_question.objects.filter(question_id = answerID, id = userid)):isfollowed = 1
                temp['isfollowed'] = isfollowed
                
                if (len(rawContent) > 140):
                    rawContent = rawContent[0:140] + '...'
                    temp['content'] = rawContent
                data['blog'+str(i+1)] = temp

            return  HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json')

        elif ('|' not in scope):    #CSC3150   group_type
            # idea, set the non-type to 0 so that not effectively return
            DBScope = []
            #get the db values
            DBtype = Blog_Questions.objects.values('group_type').order_by('id')
            for type in DBtype:   
                DBScope.append(type['group_type'])

            # start to search
            for DBitem in DBlist:
                similarity = 0
                for title in questionElem:
                    if title in DBitem:
                        similarity += 1
                answerList.append(similarity) #answerList contains all similarity in the order of id
            
            # set non-type's similarity to 0
            for i in range(len(DBScope)):
                if (DBScope[i] != scope):
                    answerList[i] = 0

            maxSimilrty = len(questionElem)
            positionList = []
            searchValue = maxSimilrty
            while(searchValue != 0):
            # positionlist contains the index of content, descending by similarity.
                for i in range(len(answerList)):    #here i is the index of the similarity list.
                    if (answerList[i] == searchValue):
                        positionList.append(i)
                #update the similarity
                searchValue -= 1

            #finially, return the searched answer
            ALL_blogs = Blog_Questions.objects.values()
            data = {}
            for i in range(len(positionList)):
                temp = ALL_blogs[positionList[i]]
                rawContent = temp['content']
                answerID = temp['id']
                amount_of_answers = Blog_Answers.objects.filter(question_id = answerID).count()
                temp['amount_of_answers'] = amount_of_answers
                isliked = 0
                if (user_like_question.objects.filter(question_id = answerID, id = userid)): isliked = 1
                temp['isliked'] = isliked

                isfollowed = 0
                if (user_follow_question.objects.filter(question_id = answerID, id = userid)):isfollowed = 1
                temp['isfollowed'] = isfollowed

                if (len(rawContent) > 140):
                    rawContent = rawContent[0:140] + '...'
                    temp['content'] = rawContent
                data['blog'+str(i+1)] = temp

            return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json')

        else:   #CSC3150|project1   sub_group_type and group_type
            scopeItem = scope.split('|')
            groupType = scopeItem[0]
            subGroupType = scopeItem[1]
            sub_group_type = sub_group.objects.filter(sub_group_name = subGroupType, group_name = groupType).values()[0]['id']

            DBScope = []
            #get the db values
            DBtype = Blog_Questions.objects.values('group_type').order_by('id')
            for type in DBtype:   
                DBScope.append(type['group_type'])

            DBsub = []
            #get the db values
            DBsubid = Blog_Questions.objects.values('sub_group_type')
            for subid in DBsubid:   
                DBsub.append(subid['sub_group_type'])

            # start to search
            for DBitem in DBlist:
                similarity = 0
                for title in questionElem:
                    if title in DBitem:
                        similarity += 1
                answerList.append(similarity) #answerList contains all similarity in the order of id
            
            # set non-type's similarity to 0
            for i in range(len(DBScope)):
                if (DBScope[i] != groupType or DBsub[i] != sub_group_type):
                    answerList[i] = 0
            # print('answerlist: ' , answerList)
            maxSimilrty = len(questionElem)
            positionList = []
            searchValue = maxSimilrty
            while(searchValue != 0):
            # positionlist contains the index of content, descending by similarity.
                for i in range(len(answerList)):    #here i is the index of the similarity list.
                    if (answerList[i] == searchValue):
                        positionList.append(i)
                #update the similarity
                searchValue -= 1

            #finially, return the searched answer
            ALL_blogs = Blog_Questions.objects.values()
            data = {}
            for i in range(len(positionList)):
                temp = ALL_blogs[positionList[i]]
                rawContent = temp['content']
                answerID = temp['id']
                amount_of_answers = Blog_Answers.objects.filter(question_id = answerID).count()
                temp['amount_of_answers'] = amount_of_answers
                isliked = 0
                if (user_like_question.objects.filter(question_id = answerID, id = userid)): isliked = 1
                temp['isliked'] = isliked

                isfollowed = 0
                if (user_follow_question.objects.filter(question_id = answerID, id = userid)):isfollowed = 1
                temp['isfollowed'] = isfollowed

                if (len(rawContent) > 140):
                    rawContent = rawContent[0:140] + '...'
                    temp['content'] = rawContent
                data['blog'+str(i+1)] = temp
            return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json')

    
# 根据hot排序，返回5个当前热门的问题
def main_page(request):
    try:
        if request.method == 'POST':
            username = request.POST['username']

            userid = User.objects.filter(username = username).values()[0]['id']

            # getting the blogs, order by 'hot'
            hot_blogs = Blog_Questions.objects.order_by('-hot').values()
            data = {}
            for i in range(0, min(10,len(hot_blogs)-1)):
                question_id = hot_blogs[i]['id']

                # check whether the current user has liked this blog_question. If the current user has liked this blog, return isliked = 1
                isliked = 0
                if (user_like_question.objects.filter(question_id = question_id, id = userid)):
                    isliked = 1

                # check whether the current user has followed this blog_question. If the current user has followed this blog, return isfollowed = 1
                isfollowed = 0
                if (user_follow_question.objects.filter(question_id = question_id, id = userid)):
                    isfollowed = 1

                # getting the url of picture of the corresponding blog
                try:
                    url = picture.objects.filter(question = question_id).values()[0]['url']
                except:
                    url = ""

                # getting the amount of answers regarding to this questions
                amount_of_answers = Blog_Answers.objects.filter(question_id = question_id).count()

                if (hot_blogs[i]['content_format'] == "Markdown"):
                    content = hot_blogs[i]["content"]
                    raw_content = get_raw(get_HTML(content))
                else:
                    raw_content = hot_blogs[i]["content"]

                if (len(raw_content) > 140):
                    raw_content = raw_content[0:140] + "..."

                # put the url, whether user has liked/followed the blog into data, preparing to be sent to frontend
                temp = hot_blogs[i]
                temp['isliked'] = isliked
                temp['isfollowed'] = isfollowed
                temp['url'] = url
                temp['content'] = raw_content
                temp['amount_of_answers'] = amount_of_answers
                data['blog'+str(i+1)] = temp
            return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json')
        else:
            return HttpResponse("Only POST-request is accepted!")
    except:
        return HttpResponse("Invalid Request! Please use Post-request and attach usename.")

# 根据用户名，返回用户关注的问题
def my_follow(request):
    try:
        if request.method == 'POST':
            username = request.POST['username']

            userid = User.objects.filter(username = username).values()[0]['id']

            # get a list of question ids the current user is following
            question_ids = user_follow_question.objects.filter(id = userid).values()

            data = {}
            for i in range (0, len(question_ids)):
                question_id = question_ids[i]['question_id']

                # getting the url of picture of the corresponding blog
                try:
                    url = picture.objects.filter(question = question_id).values()[0]['url']
                except:
                    url = ""

                # getting the amount of answers regarding to this questions
                amount_of_answers = Blog_Answers.objects.filter(question_id = question_id).count()

                # get the full content of the questions
                question = Blog_Questions.objects.filter(id = question_id).values()

                # check whether the current user has liked this blog_question. If the current user has liked this blog, return isliked = 1
                isliked = 0
                if (user_like_question.objects.filter(question_id = question_id, id = userid)):
                    isliked = 1

                # check whether the current user has followed this blog_question. If the current user has followed this blog, return isfollowed = 1
                isfollowed = 0
                if (user_follow_question.objects.filter(question_id = question_id, id = userid)):
                    isfollowed = 1

                # put the url into data, preparing to be sent to frontend
                temp = question[0]

                if (question[0]['content_format'] == "Markdown"):
                    content = question[0]["content"]
                    raw_content = get_raw(get_HTML(content))
                else:
                    raw_content = question[0]["content"]

                if (len(raw_content) > 140):
                    raw_content = raw_content[0:140] + "..."

                temp['url'] = url
                temp['isliked'] = isliked
                temp['isfollowed'] = isfollowed
                temp['content'] = raw_content
                temp['amount_of_answers'] = amount_of_answers
                data['blog'+str(i+1)] = temp

            return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json')
        else:
            return HttpResponse("Only POST-request is accepted!")
    except:
        return HttpResponse("Invalid Request! Please use Post-request and attach usename.")

# 根据用户名，返回该用户关注的分组
def my_group(request):
    try:
        if request.method == 'POST':
            username = request.POST['username']

            userid = User.objects.filter(username = username).values()[0]['id']

            group_names = user_follow_group.objects.filter(id = userid).values()

            data = {}
            for i in range(0, len(group_names)):
                group_name = group_names[i]['group_name']
                
                group = Group.objects.filter(group_name=group_name).values()[0]

                # getting the url of picture of the corresponding blog
                try:
                    url = picture.objects.filter(group_name = group_name).values()[0]['url']
                except:
                    url = ""

                temp = group
                temp['url'] = url

                data['group'+str(i+1)] = temp

            return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json')
        else:
            return HttpResponse("Only POST-request is accepted!")
    except:
        return HttpResponse("Invalid Request! Please use Post-request and attach usename.")



# /unAnswered: 按关注的数量返回高赞未回答的问题
def unAnswered(request):
    try:
        if request.method == 'POST':
            
            # get the information of current user
            username = request.POST['username']

            userid = User.objects.filter(username = username).values()[0]['id']

            cursor = connection.cursor()
            
            # get the un-unswered questions ordered by amount of follows
            cursor.execute("select * from Our_project_blog_questions where id not in (select question_id from Our_project_blog_answers) ORDER BY `follow` DESC;")
            
            # zip the raw results into a dict
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            questions_represent_by_dict = []
            for row in rows:
                questions_represent_by_dict.append(dict(zip(columns, row)))

            data = {}
            for i in range(0, len(questions_represent_by_dict)):

                # get the id of question blog
                question_id = questions_represent_by_dict[i]['id']

                # fectch the pic's url according to the question blog's id
                try:
                    url = picture.objects.filter(question = question_id).values()[0]['url']
                except:
                    url = ""

                isliked = 0
                if (user_like_question.objects.filter(question_id = question_id, id = userid)):
                    isliked = 1

                # check whether the current user has followed this blog_question. If the current user has followed this blog, return isfollowed = 1
                isfollowed = 0
                if (user_follow_question.objects.filter(question_id = question_id, id = userid)):
                    isfollowed = 1

                # put all the necessary information into the dict
                temp = questions_represent_by_dict[i]

                if (temp['content_format'] == "Markdown"):
                    content = temp["content"]
                    raw_content = get_raw(get_HTML(content))
                else:
                    raw_content = temp['content']

                if (len(raw_content) > 140):
                    raw_content = raw_content[0:140] + "..."

                temp['url'] = url
                temp['isliked'] = isliked
                temp['isfollowed'] = isfollowed
                temp['content'] = raw_content
                data['blog'+str(i+1)] = temp

            return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json')
        else:
            return HttpResponse("Only POST-request is accepted!")
    except:
        return HttpResponse("Invalid Request! Please use Post-request and attach usename.")




# allow user to like a question/answer
def like(request):
    data = {
        'ok': 0
    }
    try:
        if request.method == 'POST':
            
            username = request.POST['username']
            Question_or_Answer = request.POST['type']
            target_id = request.POST['id']
            user_id = User.objects.filter(username=username).values()[0]['id']
            if (int(Question_or_Answer)):    # means the id belong to an answer
    
                already_like = user_like_answer.objects.filter(id= user_id, answer_id = target_id).count()
                if (already_like):     # if already like, then dislike
                    user_like_answer.objects.filter(id= user_id, answer_id = target_id).delete()

                    change_amount_of_like_or_follow(target_id, Question_or_Answer = 0, follow_or_like = 0, add_or_reduce = 0)
                else:
                    user_like_answer.objects.create(id= user_id, answer_id = target_id)

                    change_amount_of_like_or_follow(target_id, Question_or_Answer = 0, follow_or_like = 0, add_or_reduce = 1)
            else:                       # means the id belong to a question

                already_like = user_like_question.objects.filter(id= user_id, question_id = target_id).count()
                if (already_like):     # if already like, then dislike
                    user_like_question.objects.filter(id= user_id, question_id = target_id).delete()

                    change_amount_of_like_or_follow(target_id, Question_or_Answer = 1, follow_or_like = 0, add_or_reduce = 0)
                else:
                    user_like_question.objects.create(id= user_id, question_id = target_id)

                    change_amount_of_like_or_follow(target_id, Question_or_Answer = 1, follow_or_like = 0, add_or_reduce = 1)

            data['ok'] = 1
        else:
            return HttpResponse("Only POST-request is accepted!")
    except:
        return HttpResponse("Invalid input!")

    return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json')
            

    

# allow user to follow a question
def follow(request):
    data = {
        'ok': 0
    }
    try:
        if request.method == 'POST':
            
            username = request.POST['username']
            target_id = request.POST['id']
            user_id = User.objects.filter(username=username).values()[0]['id']

            already_like = user_follow_question.objects.filter(id= user_id, question_id = target_id).count()
            if (already_like):     # if already like, then dislike
                user_follow_question.objects.filter(id= user_id, question_id = target_id).delete()
                change_amount_of_like_or_follow(target_id, Question_or_Answer = 1, follow_or_like = 1, add_or_reduce = 0)
            else:
                user_follow_question.objects.create(id= user_id, question_id = target_id)
                change_amount_of_like_or_follow(target_id, Question_or_Answer = 1, follow_or_like = 1, add_or_reduce = 1)

            data['ok'] = 1
        else:
            return HttpResponse("Only POST-request is accepted!")
    except:
        return HttpResponse("Invalid input!")

    return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json')


def change_amount_of_like_or_follow(target_id, Question_or_Answer, follow_or_like, add_or_reduce):
    if (follow_or_like):  # if it is follow
        num_follow = Blog_Questions.objects.filter(id=target_id).values()[0]
        num_hot = Blog_Questions.objects.filter(id=target_id).values()[0]                  
        update_blog = Blog_Questions.objects.get(id=target_id)
        if (add_or_reduce):
            update_blog.follow = num_follow['follow'] + 1
            update_blog.hot = num_hot['hot'] + 1
        else:
            update_blog.follow = num_follow['follow'] - 1
            update_blog.hot = num_hot['hot'] - 1
        update_blog.save()
    else:     # if it is like
        if (Question_or_Answer):      # if this is a question
            num_like = Blog_Questions.objects.filter(id=target_id).values()[0]
            num_hot = Blog_Questions.objects.filter(id=target_id).values()[0]                  
            update_blog = Blog_Questions.objects.get(id=target_id)
            if (add_or_reduce):       # if add
                update_blog.like = num_like['like'] + 1
                update_blog.hot = num_hot['hot'] + 1
            else:     # reduce
                update_blog.like = num_like['like'] - 1
                update_blog.hot = num_hot['hot'] - 1
            update_blog.save()
        else:                         # if this is an answer
            num_like = Blog_Answers.objects.filter(id=target_id).values()[0]                 
            update_blog = Blog_Answers.objects.get(id=target_id)
            if (add_or_reduce):       # if add
                update_blog.like = num_like['like'] + 1
            else:     # reduce
                update_blog.like = num_like['like'] - 1
            update_blog.save()

def uploadProfile(request):
    if request.method == 'POST':
        username = request.POST['username']
        profile = request.FILES.get('profile')
        profile_dir1 = '../../profiles/' + request.POST['id'] + '.jpg'
        f = open(profile_dir1, 'wb')
        for line in profile.chunks():
            f.write(line)
        f.close()
        data = {
            'profile_name': request.POST['id'] + '.jpg'
        }

        # 判断是否改用户已经有头像了
        target_user = User.objects.filter(username = username).values()[0]
        photo_url = target_user['photo']
        if (photo_url):    # 用户有旧的头像, 则在服务器上删掉
            prefix_string = ''
            for i in range(0, len(photo_url)):
                prefix_string += photo_url[i]
                if (prefix_string == 'http://175.178.34.84/'):
                    break
            delete_url = '../../' + photo_url[i+1:] 
            os.remove(delete_url)

        # 将用户头像的url更新到数据库中
        update_user = User.objects.get(username = username)
        update_user.photo = 'http://175.178.34.84/profiles/'+ request.POST['id'] + '.jpg'
        update_user.save()
        return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json')
    else:
        return HttpResponse("Only POST-request is accepted!")


def getProfile(request):
    try:
        if request.method == "POST":
            username = request.POST['username']
            
            target_user = User.objects.filter(username = username).values()

            photo_url = target_user[0]['photo']

            data = {}
            if (photo_url): # 头像不为空
                data['url'] = photo_url
            else:
                data['url'] = ''
            
            return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json')
        else:
            return HttpResponse("Only POST-request is accepted!")
    except:
        return HttpResponse("Invalid Request! Please use Post-request and attach usename.")


'''
    Receive the POST request about the group_name, username, subgroup_name
    First, return the blogs related to this group.
'''
def getGroup(request):
    try:
        if request.method == "POST":
            group_name = request.POST['group_name']
            sub_group_name = request.POST['sub_group_name']
            username = request.POST['username']
            user_id = User.objects.filter(username=username).values()[0]['id']
            
            data = {}

            sub_group_id = sub_group.objects.filter(group_name = group_name, sub_group_name = sub_group_name).values()[0]['id']

            questions = Blog_Questions.objects.filter(group_type = group_name, sub_group_type = sub_group_id).order_by('-hot').values()
            
            for i in range(0, len(questions)):
                question_id = questions[i]['id']

                # check whether the current user has liked this blog_question. If the current user has liked this blog, return isliked = 1
                isliked = 0
                if (user_like_question.objects.filter(question_id = question_id, id = user_id)):
                    isliked = 1

                # check whether the current user has followed this blog_question. If the current user has followed this blog, return isfollowed = 1
                isfollowed = 0
                if (user_follow_question.objects.filter(question_id = question_id, id = user_id)):
                    isfollowed = 1

                # getting the url of picture of the corresponding blog
                try:
                    url = picture.objects.filter(question = question_id).values()[0]['url']
                except:
                    url = ""

                # getting the amount of answers regarding to this questions
                amount_of_answers = Blog_Answers.objects.filter(question_id = question_id).count()

                # getting the sub_group_name according to the sub_group_type
                sub_group_name = sub_group.objects.filter(id = questions[i]["sub_group_type"]).values()[0]["sub_group_name"]

                if (questions[i]['content_format'] == "Markdown"):
                    content = questions[i]["content"]
                    raw_content = get_raw(get_HTML(content))
                else:
                    raw_content = questions[i]["content"]

                if (len(raw_content) > 140):
                    raw_content = raw_content[0:140] + "..."

                # put the url, whether user has liked/followed the blog into data, preparing to be sent to frontend
                temp = questions[i]
                temp['isliked'] = isliked
                temp['isfollowed'] = isfollowed
                temp['url'] = url
                temp['content'] = raw_content
                temp['sub_group_name'] = sub_group_name
                temp['amount_of_answers'] = amount_of_answers
                data['blog'+str(i+1)] = temp
                    
            return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json')
        else:
            return HttpResponse("Only POST-request is accepted!")
    except:
        return HttpResponse("Invalid Input!")


'''
    Receive the POST request about the username and group_name
    If the user has followed, then unfollow. Vice Verse
    Store/Delete the "user follow group" info into DB, add/delete the number of follow of Group by 1
    return {ok: 1} if the  
'''
def followGroup(request):
    try:
        if request.method == "POST":
            username = request.POST['username']
            group_name = request.POST['group_name']

            # get the corresponding user id
            user_id = User.objects.filter(username=username).values()[0]['id']
            
            if (user_follow_group.objects.filter(id = user_id, group_name = group_name)):
                user_follow_group.objects.filter(id= user_id, group_name = group_name).delete()
                num_follow = Group.objects.filter(group_name = group_name).values()[0]                  
                update_group = Group.objects.get(group_name= group_name)
                update_group.amount_of_follows = num_follow['amount_of_follows'] - 1
                update_group.save()
            else:
                user_follow_group.objects.create(id= user_id, group_name = group_name)
                num_follow = Group.objects.filter(group_name = group_name).values()[0]                  
                update_group = Group.objects.get(group_name= group_name)
                update_group.amount_of_follows = num_follow['amount_of_follows'] + 1
                update_group.save()
            data = {}
            data["ok"] = 1

            return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json')
        else:
            return HttpResponse("Only POST-request is accepted!")
    except:
        return HttpResponse("Invalid Request! Please use Post-request and attach usename and group name.")


'''
    Receive the POST request about the username
    Return all the groups, as well as each's description, url of picture, 
    number of follows, and whether the current user follow
    default own = 0 means return all the groups, own = 1 means only return the groups that current user follows
'''
def groups(request, own = 0):
    try:
        if request.method == "POST":
            data = {}
            username = request.POST['username']
            user_id = User.objects.filter(username=username).values()[0]['id']

            groups = Group.objects.values()

            n_group = 0
            for i in range(0, len(groups)):
                group = groups[i]
                group_name = group["group_name"]

                # get the url of picture of this group
                try:
                    url = picture.objects.filter(group_name = group_name).values()[0]['url']
                except:
                    url = ""

                
                # check whether the current user has followed this group
                isFollowed = 0
                if (user_follow_group.objects.filter(id = user_id, group_name = group_name)):
                    isFollowed = 1
                else: 
                    if (own == 1):
                        continue

                temp = group
                temp["isFollowed"] = isFollowed
                temp["url"] = url

                # get the corresponding sub-groups' name of this group, and assemble them into the return data
                sub_groups = sub_group.objects.filter(group_name = group_name).values()
                name_of_subgroups = []
                sub_groups_names = {}
                for j in range(0, len(sub_groups)):
                    sub_groups_names["subgroup" + str(j+1)] = sub_groups[j]["sub_group_name"]

                temp["sub_groups"] = sub_groups_names
                data["group" + str(n_group+1)] = temp
                n_group += 1

            return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json')
        else:
            return HttpResponse("Only POST-request is accepted!")
    except:
        return HttpResponse("Invalid Request! Please use Post-request and attach usename.")


'''
    Inherit from groups(),
    return only the groups that the current user is following
'''
def MyGroups(request): 
    try:
        response = groups(request, own = 1)
        return response
    except:
        return HttpResponse("Invalid Request! Please use Post-request and attach usename.")



'''
    Gives the question id and username, 
    return all the contents of questions. Including convert the mardown format into the HTML one. 
'''
def GetQuestions(request):
    
    try:
        if request.method == "POST":
            question_id = request.POST["question_id"]
            username = request.POST["username"]
            userid = User.objects.filter(username=username).values()[0]['id']
            
            question = Blog_Questions.objects.filter(id = question_id).values()[0]

            # check whether the current user has liked this blog_question. If the current user has liked this blog, return isliked = 1
            isliked = 0
            if (user_like_question.objects.filter(question_id = question_id, id = userid)):
                isliked = 1

            # check whether the current user has followed this blog_question. If the current user has followed this blog, return isfollowed = 1
            isfollowed = 0
            if (user_follow_question.objects.filter(question_id = question_id, id = userid)):
                isfollowed = 1

            # getting the url of picture of the corresponding blog
            pics = picture.objects.filter(question = question_id).values()
            pic_urls = {}
            for i in range(0, len(pics)):
                pic_urls["url" + str(1+i)] = pics[i]["url"]

            # find the files attached to this question
            files = file.objects.filter(corresponding_question = question_id).values()
            file_urls = {}
            for i in range(0, len(files)):
                file_urls["url" + str(1+i)] = files[i]["url"]

            # getting the amount of answers regarding to this questions
            amount_of_answers = Blog_Answers.objects.filter(question_id = question_id).count()

            content = question["content"]
            if (question["content_format"] == "Markdown"):
                html_content = get_HTML(content)
            else:
                html_content = content

            # get the sub_group_name

            sub_group_name = sub_group.objects.filter(id = question["sub_group_type"]).values()[0]["sub_group_name"]

            author_id = question["author_id"]
            author = User.objects.filter(id = author_id).values()[0]
            author_name = author["username"]
            author_profile = author["photo"]
            

            # put the url, whether user has liked/followed the blog into data, preparing to be sent to frontend
            temp = question
            temp['content'] = html_content
            temp['isliked'] = isliked
            temp['isfollowed'] = isfollowed
            temp['pic_urls'] = pic_urls
            temp['file_urls'] = file_urls
            temp['amount_of_answers'] = amount_of_answers
            temp["sub_group_name"] = sub_group_name
            temp["author_name"] = author_name
            temp["author_profile"] = author_profile

            data = temp
            
            return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json')
        else:
            return HttpResponse("Only POST-request is accepted!")
    except:
        return HttpResponse("Invalid Request! Please use Post-request and attach usename and question id.")


'''
    Gives the content formated by markdown,
    return the content formated by HTML
'''
def get_HTML(md_content):
    HTML_content = markdown.markdown(md_content, 
            extensions = [
                'markdown.extensions.extra',
                'markdown.extensions.codehilite',
            ])
    return HTML_content

'''
    Get the HTML format of content, return the raw data. 
'''
def get_raw(HTML_content):
    raw_data = ""
    deleting = False
    stop_point = 0
    newline = False
    for i in range(0, len(HTML_content)):
        if (HTML_content[i] == "<"):
            if (deleting == False):
                deleting = True
                stop_point = i
            else:
                deleting = False
                raw_data += HTML_content[stop_point:i-1]
        if (deleting == False):
            if (HTML_content[i] == "\n"):
                if (newline == False):
                    newline = True
                else:
                    continue  
            else:
                newline = False
            raw_data += HTML_content[i]
        if (HTML_content[i] == ">"):
            if (deleting == True):
                deleting = False

    return raw_data

'''
    Given the username, Question ID,
    gives all the contents related to this question.
    Specially, maybe there will be answers which answer to another answer, it should be also included
'''
def GetAnswers(request):

    if request.method == "POST":
        data = {}

        username = request.POST['username']
        userid = User.objects.filter(username=username).values()[0]['id']

        question_id = request.POST['question_id']

        Answers = Blog_Answers.objects.filter(question_id = question_id).order_by("id").values()
        index_root_answer = Blog_Answers.objects.filter(question_id = question_id, father_answer_id = None).count()

        for i in range(0, len(Answers)):
            answer = Answers[i]
            answer_id = answer['id']

            # check whether the current user has liked this blog_question. If the current user has liked this blog, return isliked = 1
            isliked = 0
            if (user_like_answer.objects.filter(answer_id = answer_id, id = userid)):
                isliked = 1

            # getting the url of picture of the corresponding blog
            pics = picture.objects.filter(answer = answer_id).values()
            pic_urls = {}
            for i in range(0, len(pics)):
                pic_urls["url" + str(1+i)] = pics[i]["url"]

            # find the files attached to this question
            files = file.objects.filter(corresponding_answer = answer_id).values()
            file_urls = {}
            for i in range(0, len(files)):
                file_urls["url" + str(1+i)] = files[i]["url"]

            content = answer["content"]
            if (answer["content_format"] == "Markdown"):
                html_content = get_HTML(content)
            else:
                html_content = content

            # according to the author id, return the author's profile url and username
            author_id = answer["author_id"]
            author_name = User.objects.filter(id = author_id).values()[0]['username']
            profile_url = User.objects.filter(id = author_id).values()[0]['photo']

            # put the url, whether user has liked/followed the blog into data, preparing to be sent to frontend
            answer['content'] = html_content
            answer['isliked'] = isliked
            answer['pic_urls'] = pic_urls
            answer['file_urls'] = file_urls
            answer['author_name'] = author_name
            answer['author_profile_url'] = profile_url
            answer['Children'] = {}

            if answer["father_answer_id"] == None:   # means it is the root answer
                data["root" + str(answer_id)] = answer
            else:
                root_id = answer["father_answer_id"]
                father_id = Blog_Answers.objects.filter(id = root_id).values()[0]["author_id"]
                father_name = User.objects.filter(id = father_id).values()[0]['username']
                father = answer
                target_id = -1
                while (father != None):
                    root_id = father["father_answer_id"]
                    target_id = father['id']
                    try:
                        father = Blog_Answers.objects.filter(id = root_id).values()[0]  
                    except:
                        break
                child = answer
                child["father_name"] = father_name
                data["root" + str(target_id)]['Children']["child" + str(answer_id)] = child

        return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json')
    else:
        return HttpResponse("Only POST-request is accepted!")



'''
    Reveice piece of code, compile it and run it on internet,
    return the result back
'''
def run_code(request):
    try:
        if request.method == "POST":
            source = request.POST['source_code']
            try:
                lang = request.POST['lang']
            except:
                lang = "Python"

            accessToken = '988ee724e12e4b4add3d9b8baf105b56'
            endpoint = 'c63f7566.compilers.sphere-engine.com'

            client = CompilersClientV4(accessToken, endpoint)

            compiler = 116   # default python
            if (lang == "Python"):
                compiler = 116
            elif (lang == "Assembler"):
                compiler = 45
            elif (lang == "C"):
                compiler = 11
            elif (lang == "C#"):
                compiler = 86
            elif (lang == "C++"):
                compiler = 1
            elif (lang == "Fortran"):
                compiler = 5
            elif (lang == "Go"):
                compiler = 114
            elif (lang == "Java"):
                compiler = 10
            elif (lang == "R"):
                compiler = 117
            elif (lang == "Rust"):
                compiler = 93
            elif (lang == "Javascript"):
                compiler = 35
            elif (lang == "Bash"):
                compiler = 28

            input = '111'

            response = client.submissions.create(source, compiler, input)

            task_id = response.get("id")
            response = client.submissions.get(task_id)

            executing_status = response.get("executing")

            while (executing_status):
                response = client.submissions.get(task_id)
                executing_status = response.get("executing")

            time = response.get("result").get("time")
            memory = response.get("result").get("memory")
            try:
                uri=response.get("result").get("streams").get("output").get('uri')
            except:
                try:
                    uri=response.get("result").get("streams").get("error").get('uri')
                except:
                    uri=response.get("result").get("streams").get("cmpinfo").get('uri')
            contents = urllib.request.urlopen(uri).read().decode('utf-8')

            data = {}
            contents = "Result: \n" + contents
            if (compiler == 116):
                contents += "-----------------------------------------------\n" + "Running Time: " + str(time) + "s\nMemory Used: " + str(memory) + " Bytes."
            else:
                contents += "\n-----------------------------------------------\n" + "Running Time: " + str(time) + "s\nMemory Used: " + str(memory) + " Bytes."
            data["result"] = contents

            return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json')
        else:
            return HttpResponse("Only POST-request is accepted!")
    except:
        return HttpResponse("Invalid Request! Please use Post-request and attach usename.")
    
'''
    Given username
    return the blogs this user post before. 
'''
def MyBlogs(request):
    data = {}
    if request.method == "POST":
        username = request.POST["username"]
        try:
            userid = User.objects.filter(username = username).values()[0]['id']
        except:
            data['ok'] = 0
            return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json') 
        questions = Blog_Questions.objects.filter(author_id = userid).values()
        for i in range(0, len(questions)):

            question_id = questions[i]['id']

            # check whether the current user has liked this blog_question. If the current user has liked this blog, return isliked = 1
            isliked = 0
            if (user_like_question.objects.filter(question_id = question_id, id = userid)):
                isliked = 1

            # check whether the current user has followed this blog_question. If the current user has followed this blog, return isfollowed = 1
            isfollowed = 0
            if (user_follow_question.objects.filter(question_id = question_id, id = userid)):
                isfollowed = 1

            # getting the url of picture of the corresponding blog
            try:
                url = picture.objects.filter(question = question_id).values()[0]['url']
            except:
                url = ""

            # getting the amount of answers regarding to this questions
            amount_of_answers = Blog_Answers.objects.filter(question_id = question_id).count()

            if (questions[i]['content_format'] == "Markdown"):
                content = questions[i]["content"]
                raw_content = get_raw(get_HTML(content))
            else:
                raw_content = questions[i]["content"]

            if (len(raw_content) > 140):
                raw_content = raw_content[0:140] + "..."

            # put the url, whether user has liked/followed the blog into data, preparing to be sent to frontend
            temp = questions[i]
            temp['isliked'] = isliked
            temp['isfollowed'] = isfollowed
            temp['url'] = url
            temp['content'] = raw_content
            temp['amount_of_answers'] = amount_of_answers
            data['blog'+str(i+1)] = temp

    else:
        return HttpResponse("This API only accept POST request!")

    return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json') 

'''
    Given the username, question_id, father_answer_id, content, code, lang, content_format.
    Store all of this informations into the DB
'''          
def Reply(request):
    data = {}
    data["ok"] = 0
    if request.method == "POST":
        username = request.POST["username"]

        # store the user_id instead of the username
        userid = User.objects.filter(username = username).values()[0]["id"]

        question_id = request.POST["question_id"]
        if (question_id == ""):
            question_id = None
        else:
            question_id = int(question_id)

        father_answer_id = request.POST["father_answer_id"]
        if (father_answer_id == ""):
            father_answer_id = None
        else:
            father_answer_id = int(father_answer_id)

        try:
            fs_url = request.POST['files_url']
            print(fs_url)
        except:
            fs_url = ""
            print("nothing")
        
        content = request.POST["content"]
        content_format = "HTML"

        Answer = Blog_Answers.objects.create(question_id=question_id, father_answer_id=father_answer_id, content=content, content_format = content_format, like = 0, author_id = userid)
        answer_id = Answer.id

        for i in range(0, len(fs_url)):
            if fs_url[i] == ".":
                extension = fs_url[i:]

        if (fs_url != ""):
            print(extension)
            if (extension == ".jpg" or extension == ".png" or extension == ".JPG" or extension == ".PNG" or extension == ".GIF" or extension == ".gif" or extension == ".JPEG" or extension == ".jpeg"):
                pic = picture.objects.create(url = fs_url, answer = answer_id, group_name = None)
            else:
                fs = file.objects.create(url = fs_url, corresponding_answer = answer_id)

        # If the reply has pictures and files, upload them
        data["ok"] = 1
    else:
        data['ok'] = 0

    return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json')  




'''
    Add views by one
'''
def AddViews(request):
    data = {}
    data['ok'] = 0
    if request.method == "POST":
        question_id = request.POST["question_id"]

        question = Blog_Questions.objects.get(id=question_id)
        question.views = question.views + 1
        question.hot = question.hot + 1
        question.save()
        data['ok'] = 1
    return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json')




def get_file(request):
    data= {}
    recevie_file = request.FILES.get("file")
    username = request.POST.get("username")

    userid = User.objects.filter(username = username).values()[0]['id']

    name = recevie_file.name
    for i in range(0, len(name)):
        if name[i] == ".":
            extension = name[i:]

    code = encode(10)
    if (extension == ".jpg" or extension == ".png" or extension == ".JPG" or extension == ".PNG" or extension == ".GIF" or extension == ".gif" or extension == ".JPEG" or extension == ".jpeg"):
        fs_dir = '../../pictures/pics/' + code + extension
        data["link"] = 'http://175.178.34.84/pics/' + code + extension
    else:
        fs_dir = '../../fs/' + code + extension
        data["link"] = 'http://175.178.34.84/fs/' + code + extension
    f = open(fs_dir, 'wb')
    for line in recevie_file.chunks():
        f.write(line)
    f.close()

    return HttpResponse(json.dumps(data , cls=ComplexEncoder), content_type='application/json')


'''
    Defining the test cases
'''
def testing(request):

    result = {}

    result['Unit_test'] = Unit_Test.test()

    result['Component_test'] = Component_Test.test()

    result['System_test'] = System_Test.test()

    delete_test_insert()

    return HttpResponse(json.dumps(result , cls=ComplexEncoder), content_type='application/json')

def delete_test_insert():
    Blog_Questions.objects.filter(title='How to be a perfect test engineer?').delete()

def filter_word(blog_list):
  blog_id = blog_list[0]
  blog_title = blog_list[1]
  blog_content = blog_list[2]

  # load the deep learning dataset
  nlp = spacy.load('en_core_web_sm')

  doc_title = nlp(blog_title)
  doc_content = nlp(blog_content)

  #创建字典 {token名字：出现的次数}
  token_dict = {}

  #遍历标题所有数据
  for token in doc_title:
    if not (token.is_punct or token.is_stop): # if not a punctuation or a stop word
      lemma_token = token.lemma_ # transform it to normal form (lemma)
      if lemma_token in token_dict:
        token_dict[lemma_token][0] += 1
      else:
        token_dict[lemma_token] = [1,0]
  
  #遍历内容所有数据
  for token in doc_content:
    if not (token.is_punct or token.is_stop): # if not a punctuation or a stop word
      lemma_token = token.lemma_ # transform it to normal form (lemma)
      if lemma_token in token_dict:
        token_dict[lemma_token][1] += 1
      else:
        token_dict[lemma_token] = [0,1]

  result_list = []

  for (key,value) in token_dict.items():
    mylist = []
    mylist.append(key)
    mylist.append(blog_id)
    mylist.append(value[0])
    mylist.append(value[1])
    result_list.append(mylist)

  return result_list

def search_spilt(title):
  nlp = spacy.load('en_core_web_sm')
  
  doc_title = nlp(title)

  token_dict = {}

  for token in doc_title:
    if not (token.is_punct or token.is_stop):
      lemma_token = token.lemma_
      if lemma_token in token_dict:
        token_dict[lemma_token] += 1
      else:
        token_dict[lemma_token] = 1
  
  word_list = []
  count_list = []
  dim = 0
  for (key,value) in token_dict.items():
    dim += 1
    word_list.append(key)
    count_list.append(value)
  
  result = [dim, word_list,count_list]

  return result


# quick sort
def quicksort_blog(dim, target_vec, blog_vec_list, l, r):
    if(l < r):
        pivot = partition(dim, target_vec, blog_vec_list, l, r)
        quicksort_blog(dim, target_vec, blog_vec_list, l, pivot - 1)
        quicksort_blog(dim, target_vec, blog_vec_list, pivot + 1, r)
    return blog_vec_list

def partition(dim, target_vec, blog_vec_list, l, r):
    pivot = r
    i = l
    for j in range(l,r):
        if innerProduct(dim, blog_vec_list[j], target_vec) > innerProduct(dim, blog_vec_list[pivot], target_vec):
            blog_vec_list[j], blog_vec_list[i] = blog_vec_list[i], blog_vec_list[j]
            i += 1

    blog_vec_list[i], blog_vec_list[pivot] = blog_vec_list[pivot], blog_vec_list[i]

    return i


def innerProduct(dim, blog_vec, target_vec):
  result = 0
  for i in range(1, dim+1):
    result += target_vec[i-1] * blog_vec[i]

  return result 
