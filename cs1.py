import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import json,pytz
import base64


# Logo
st.logo("img/微信图片_logo.jpg")
# 设置页面的配置项
st.set_page_config(
    page_title="AI智能助手",
    page_icon="👽",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)


# 生成会话标识函数
def generate_session_name():
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    now = datetime.now(tz=shanghai_tz)
    return now.strftime("%Y-%m-%d_%H-%M-%S")


def save_session():
    if st.session_state.current_session:
        session_data = {
            "nick_name": st.session_state.nick_name,
            "current_session": st.session_state.current_session,
            "messages": st.session_state.messages
        }
        if not os.path.exists("sessions"):
            os.mkdir("sessions")
        with open(f"sessions/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)


def load_sessions():
    session_list = []
    if os.path.exists("sessions"):
        file_list = os.listdir("sessions")
        for filename in file_list:
            if filename.endswith(".json"):
                session_list.append(filename[:-5])
    session_list.sort(reverse=True)
    return session_list[:3]


def load_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            with open(f"sessions/{session_name}.json", "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.messages = session_data["messages"]
                st.session_state.nick_name = session_data["nick_name"]
                st.session_state.current_session = session_name
                st.session_state.upload_key_counter += 1
    except Exception:
        st.error("加载会话失败!")


def delete_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            os.remove(f"sessions/{session_name}.json")
            if session_name == st.session_state.current_session:
                st.session_state.messages = []
                st.session_state.current_session = generate_session_name()
                st.session_state.upload_key_counter += 1
    except Exception:
        st.error("删除会话失败!")


def file_to_base64(file):
    return base64.b64encode(file.read()).decode('utf-8')


def get_media_type(filename):
    ext = filename.split('.')[-1].lower()
    image_exts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']

    if ext in image_exts:
        return 'image'
    return 'unknown'


# ========== 初始化所有 Session State ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
if "nick_name" not in st.session_state:
    st.session_state.nick_name = "编程高手"
if "current_session" not in st.session_state:
    st.session_state.current_session = generate_session_name()
if "upload_key_counter" not in st.session_state:
    st.session_state.upload_key_counter = 0

st.title("AI智能小周")

client = OpenAI(
    api_key="sk-085de50014b743cdb13a0075793a366e",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

with st.sidebar:
    st.subheader("AI控制面板")

    if st.button("新建会话", use_container_width=True, icon="✏️"):
        save_session()
        if st.session_state.messages:
            st.session_state.messages = []
            st.session_state.current_session = generate_session_name()
            st.session_state.upload_key_counter += 1
            save_session()
            st.rerun()

    st.text("会话历史")
    session_list = load_sessions()
    for session in session_list:
        col1, col2 = st.columns([4, 1])
        with col1:
            is_current = session == st.session_state.current_session
            if st.button(session, use_container_width=True, icon="📄",
                         key=f"load_{session}",
                         type="primary" if is_current else "secondary"):
                load_session(session)
                st.rerun()
        with col2:
            if st.button("", use_container_width=True, icon="❌", key=f"delete_{session}"):
                delete_session(session)
                st.rerun()

    st.divider()
    st.subheader("身份信息")
    nick_name = st.text_input("角色", placeholder="请输入角色信息", value=st.session_state.nick_name)
    if nick_name:
        st.session_state.nick_name = nick_name

    st.divider()
    st.subheader("模型设置")
    model_option = st.selectbox(
        "选择模型",
        ["qwen-vl-max", "qwen-vl-plus"],
        index=0,
        help="qwen-vl-max: 最强多模态（支持图片识别）"
    )

system_prompt = """
        你叫小周，现在是%s，请完全代入角色。
        规则：
            1. 每次只回1条消息
            2. 禁止任何场景或状态描述性文字
            3. 匹配用户的语言
            4. 有需要的话可以用emoji表情
            5. 回复的内容, 要充分体现性格特征
            6. 如果用户发送了图片，请仔细观察并描述内容，保持角色的口吻进行评论
        性格：
            - 闷骚抽象
        你必须严格遵守上述规则来回复用户。
    """

st.text(f"当前会话: {st.session_state.current_session}")

# ========== 关键修改：固定高度的消息区域 ==========
# 计算合适的高度：视口高度减去底部固定区域的高度（约250px）
# 使用 calc(100vh - 280px) 实现自适应
messages_container = st.container(height=420)  # 固定高度，可滚动

with messages_container:
    # 展示历史消息
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if isinstance(message["content"], str):
                st.write(message["content"])
            elif isinstance(message["content"], list):
                text_content = ""
                for item in message["content"]:
                    if item.get("type") == "text":
                        text_content = item.get("text", "")
                    elif item.get("type") == "image_url":
                        image_url = item.get("image_url", {}).get("url", "")
                        st.image(image_url, width=300)
                    elif item.get("type") == "video_url":
                        video_url = item.get("video_url", {}).get("url", "")
                        st.video(video_url)
                if text_content:
                    st.write(text_content)

# ========== 底部固定区域（上传 + 输入）==========
# 现在 upload_container 和 chat_input 会固定在页面底部
upload_container = st.container(border=True)
current_upload_key = f"file_uploader_{st.session_state.upload_key_counter}"

with upload_container:
    uploaded_file = st.file_uploader(
            "上传图片",
            type=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
            accept_multiple_files=False,
            key=current_upload_key,
            label_visibility="collapsed"  # 隐藏标签，更简洁
    )


# 输入框（固定在页面最底部）
prompt = st.chat_input("请输入您要问的问题...")

# 处理发送逻辑
if prompt or (prompt == "" and uploaded_file is not None):
    user_content = []

    if prompt:
        user_content.append({"type": "text", "text": prompt})

    if uploaded_file is not None:
        file_type = get_media_type(uploaded_file.name)
        uploaded_file.seek(0)
        base64_data = file_to_base64(uploaded_file)

        if file_type == "image":
            mime_type = f"image/{uploaded_file.name.split('.')[-1]}"
            if mime_type == "image/jpg":
                mime_type = "image/jpeg"
            image_url = f"data:{mime_type};base64,{base64_data}"

            user_content.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })

        # 发送后重置上传器
        st.session_state.upload_key_counter += 1

    if user_content:
        st.session_state.messages.append({"role": "user", "content": user_content})

    # 调用 AI
    try:
        api_messages = [{"role": "system", "content": system_prompt % st.session_state.nick_name}]
        for msg in st.session_state.messages:
            api_messages.append(msg)

        with st.chat_message("assistant"):
            response_container = st.empty()
            full_response = ""

            stream = client.chat.completions.create(
                model=model_option,
                messages=api_messages,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    response_container.markdown(full_response + "▌")

            response_container.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})
        save_session()
        st.rerun()

    except Exception as e:
        st.error(f"调用出错: {str(e)}")