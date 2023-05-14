import json, uvicorn, requests, base64, io
from PIL import Image, PngImagePlugin
from fastapi import FastAPI, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from front_end_utils import *

app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)
history = []
chatmsg=  ""

@app.get("/api/repeat")
def repeat():
    global history, chatmsg
    request = chatglm_json(str(chatmsg), history=history)
    request_list = json.loads(request)
    response = request_list.get('response')
    return Response(f"{response}")

@app.get("/api/chat")
def chat(prompt: str):
    global history, chatmsg
    request = chatglm_json(str(f"我的问题是“{prompt}”，请选出下列内容中最符合的一项 A. 聊天  B.画图，请直接回复答案（A或B），不需要回复原因"), history=[])
    chatmsg = prompt
    request_list = json.loads(request)
    response = request_list.get('response')
    print(response)
    if "b" in response or "B" in response:
        prompt_history = [["我接下来会给你一些作画的指令，你只要回复出作画内容及对象，不需要你作画，不需要给我参考，不需要你给我形容你的作画内容，请直接给出作画内容，你不要回复”好的，我会画一张“等不必要的内容，你只需回复作画内容。你听懂了吗","听懂了。请给我一些作画的指令。"]]
        request = chatglm_json(str(f"不需要你作画，不需要给我参考，不需要你给我形容你的作画内容，请给出“{prompt}”中的作画内容，请直接给出作画内容和对象"), prompt_history)
        request_list = json.loads(request)
        draw_object = request_list.get('response')
        if draw_object[0] == "，" or draw_object[0] == "," or draw_object[0] == "。" or draw_object[0] == ".":
             draw_object = draw_object[1:len(draw_object)]
        if draw_object[-1] == "，" or draw_object[-1] == "," or draw_object[-1] == "。" or draw_object[-1] == ".":
            draw_object = draw_object[0:len(draw_object)-1]
        draw_object = draw_object.replace("好的", "")
        draw_object = draw_object.replace("我", "")
        draw_object = draw_object.replace("将", "")
        draw_object = draw_object.replace("会", "")
        draw_object = draw_object.replace("画", "")
        if draw_object[0] == "，" or draw_object[0] == "," or draw_object[0] == "。" or draw_object[0] == ".":
            draw_object = draw_object[1:len(draw_object)]
        if draw_object[-1] == "，" or draw_object[-1] == "," or draw_object[-1] == "。" or draw_object[-1] == ".":
            draw_object = draw_object[0:len(draw_object)-1]
        stable_diffusion(str(translate(draw_object)),"",5)
        request = chatglm_json(f"请介绍一下你画的关于{draw_object}", prompt_history)
        request_list = json.loads(request)
        detail = request_list.get('response')
        return Response('[SD IMAGE]'+str(detail))
    else:
        if '什么' in prompt or '怎么' in prompt or '？' in prompt or '?' in prompt :
            feature = get_config().get('Web').get('feature') #['知乎专栏','知乎回复','百科','微信公众号','新闻','B站专栏','CSDN','GitHub','All(Preview)']
            search_resp = search_main(str(prompt), feature)
            web_info = search_resp[1]
            references = search_resp[0]
            print(search_resp)
            ask_prompt = f'我的问题是“{prompt}”\n我在{references}上查询到了一些网络上的参考信息“{web_info}”\n请根据我的问题，参考我给与的信息以及你的理解进行回复'
            request = chatglm_json(str(ask_prompt), [])
            request_list = json.loads(request)
            response = request_list.get('response')
            history.append([prompt, response])
            if len(history) > 10: 
                history.pop(0)
            print(history)
            return Response(f"{response}\n\n出处:\n  {references}")
        else:
            request = chatglm_json(str(prompt), history)
            request_list = json.loads(request)
            response = request_list.get('response')
            history.append([prompt, response])
            if len(history) > 10: 
                history.pop(0)
            print(history)
            return Response(f"{response}")

@app.post("/api/stop")
def stop():
    return Response("User Interrupt")

@app.post("/api/delete")
def delete():
    global chatmsg
    chatmsg = []
    return Response("User Interrupt")

@app.get("/api/sdimg")
def image():
    data = open('./src/assets/imgs/stable_diffusion.png', mode="rb")
    return StreamingResponse(data, media_type="image/png")


if __name__ == '__main__':
    uvicorn.run("front_end:app",reload=True,port=8003)