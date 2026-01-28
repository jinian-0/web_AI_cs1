import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import json,pytz

# 设置页面的配置项
st.set_page_config(
    page_title="AI智能助手",
    page_icon="👽",
    layout="wide", # 布局
    initial_sidebar_state="expanded", # 控制的是侧边栏的状态
    menu_items={}
)

# 生成会话标识函数
def generate_session_name():
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    now = datetime.now(tz=shanghai_tz)
    return now.strftime("%Y-%m-%d_%H-%M-%S")

# 保存会话信息函数
def save_session():
    if st.session_state.current_session:
        # 构建新的会话对象
        session_data = {
            "nick_name": st.session_state.nick_name,
            "current_session": st.session_state.current_session,
            "messages": st.session_state.messages
        }

        # 如果 sessions 目录不存在, 则创建
        if not os.path.exists("sessions"):
            os.mkdir("sessions")

        # 保存会话数据
        with open(f"sessions/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

# 加载所有的会话列表信息
def load_sessions():
    session_list = []
    # 加载sessions目录下的文件
    if os.path.exists("sessions"):
        file_list = os.listdir("sessions")
        for filename in file_list:
            if filename.endswith(".json"):
                session_list.append(filename[:-5])
    session_list.sort(reverse=True) # 排序, 降序排列
    return session_list[:3]

# 加载指定的会话信息
def load_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            # 读取会话数据
            with open(f"sessions/{session_name}.json", "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.messages = session_data["messages"]
                st.session_state.nick_name = session_data["nick_name"]
                st.session_state.current_session = session_name
    except Exception:
        st.error("加载会话失败!")

# 删除会话信息函数
def delete_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            os.remove(f"sessions/{session_name}.json") # 删除文件
            # 如果删除的是当前会话, 则需要更新消息列表
            if session_name == st.session_state.current_session:
                st.session_state.messages = []
                st.session_state.current_session = generate_session_name()
    except Exception:
        st.error("删除会话失败!")



# 大标题
st.title("AI智能小周")

# Logo
st.logo("img/微信图片_logo.jpg")

# 系统提示词
system_prompt = """
        你叫 小周，你现在是%s，请完全代入角色。
        规则：
            1. 每次只回1条消息
            2. 禁止任何场景或状态描述性文字
            3. 匹配用户的语言
            4. 有需要的话可以用emoji表情
        性格：
            - 闷骚抽象安徽男孩
        你必须严格遵守上述规则来回复用户。
    """

# 初始化聊天信息
if "messages" not in st.session_state:
    st.session_state.messages = []
# 昵称
if "nick_name" not in st.session_state:
    st.session_state.nick_name = "编程高手"

# 会话标识
if "current_session" not in st.session_state:
    st.session_state.current_session = generate_session_name()

# 展示聊天信息
st.text(f"会话名称: {st.session_state.current_session}")
for message in st.session_state.messages: # {"role": "user", "content": prompt}
    st.chat_message(message["role"]).write(message["content"])

# 创建与AI大模型交互的客户端对象
client = OpenAI(api_key="sk-085de50014b743cdb13a0075793a366e",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")




# 左侧的侧边栏 - with: streamlit中上下文管理器
with st.sidebar:
    # 会话信息
    st.subheader("AI控制面板")

    # 新建会话
    if st.button("新建会话", width="stretch", icon="✏️"):
        # 1. 保存当前会话信息
        save_session()

        # 2. 创建新的会话
        if st.session_state.messages: # 如果聊天信息非空, True; 否则,  False
            st.session_state.messages = []
            st.session_state.current_session = generate_session_name()
            save_session()
            st.rerun()  # 重新运行当前页面

    # 会话历史
    st.text("会话历史")
    session_list = load_sessions()
    for session in session_list:
        col1,col2 = st.columns([4,1])
        with col1:
           # 加载会话信息
           # 三元运算符: 如果条件为真, 则返回第一个表达式的值; 否则, 返回第二个表达式的值 --> 语法: 值1 if 条件 else 值2
           if st.button(session, width="stretch", icon="📄", key=f"load_{session}", type="primary" if session == st.session_state.current_session else "secondary"):
               load_session(session)
               st.rerun()
        with col2:
            # 删除会话信息
            if st.button("", width="stretch", icon="❌️", key=f"delete_{session}"):
                delete_session(session)
                st.rerun()

    # 分割线
    st.divider()

    # 伴侣信息
    st.subheader("身份信息")
    # 昵称输入框
    nick_name = st.text_input("技能", placeholder="请输入昵称", value=st.session_state.nick_name)
    if nick_name:
        st.session_state.nick_name = nick_name



# 消息输入框
prompt = st.chat_input("请输入您要问的问题")
if prompt: # 字符串会自动转换为布尔值, 如果字符串非空, 则为True; ""否则为False
    st.chat_message("user").write(prompt)

    # 保存用户输入的提示词
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 调用AI大模型
    response = client.chat.completions.create(
        model="qwen-max",
        messages=[
            {"role": "system", "content": system_prompt % (st.session_state.nick_name)},
            *st.session_state.messages
        ],
        extra_body={"enable_search": True, "search_options": {"search_strategy": "max"}},
        stream=True
    )

    # 输出大模型返回的结果 (流式输出的解析方式)
    response_message = st.empty() # 创建一个空的组件, 用于展示大模型返回的结果

    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            full_response += content
            response_message.chat_message("assistant").write(full_response)

    # 保存大模型返回的结果
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # 保存会话信息
    save_session()