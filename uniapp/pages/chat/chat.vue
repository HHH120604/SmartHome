<template>
	<!-- 页面根容器 -->
	<view class="container">
		<!-- 背景图片和遮罩 -->
		<image class="bg" src="../../static/img/home_bg.png" mode="aspectFill"></image>
		<view class="overlay"></view>
		
		<!-- 自定义声明组件，通过ref引用为"dialog" -->
		<statement ref="dialog"></statement>
		
		<!-- 聊天区域，id为"test"，通过ref引用为"chatbox" -->
		<view class="chat_area" id="test" ref="chatbox">
			<!-- 当前时间显示区域，仅当chatList有内容时显示 -->
			<view class="current_time" v-show="chatList.length>0">
				{{currentDate}}  <!-- 显示当前日期 -->
			</view>
			
			<!-- 左侧消息容器（机器人消息） -->
			<view class="left_box">
				<!-- 内容容器 -->
				<view class="content_box">
					<!-- 内容区域，使用post样式 -->
					<view class="content post">
						<!-- 欢迎消息 -->
						<view>我是您的智能家居助手，很高兴为您服务。</view>
						<view>您可以这样提出需求：</view>
						<!-- 示例问题区域 -->
						<view class="post_request">
							<!-- 遍历postRequest数组生成示例问题 -->
							<view v-for="(item,index) in postRequest" :key="index">
								<!-- 可点击的问题文本，点击触发tapQuestion方法 -->
								<text class="active" @click="tapQuestion(item)">
									{{item.id}}.{{item.text}}</text>
							</view>
						</view>
					</view>
				</view>
			</view>
			
			<!-- 遍历chatList数组生成聊天记录 -->
			<view v-for="(item,i) in chatList" :key="i">
				<!-- 如果是助手(assistant)的消息，使用左侧布局 -->
				<view class="left_box" v-if="item.role == 'assistant'">
					<!-- 内容容器 -->
					<view class="content_box">
						<!-- 使用v-html渲染内容，通过htmlContent方法处理 -->
						<view class="content" v-html="htmlContent(item.content)">
						</view>
					</view>
				</view>

				<!-- 如果是用户(user)的消息，使用右侧布局 -->
				<view class="right_box" v-if="item.role == 'user'">
					<!-- 内容容器 -->
					<view class="content_box">
						<!-- 显示用户消息内容 -->
						<view class="content">
							{{item.content}}
						</view>
					</view>
				</view>
			</view>

			<!-- 加载指示器组件，根据showLoading状态显示/隐藏 -->
			<view v-if="showLoading && !showTimeoutError && !showConnectionError" class="loading-container">
				<u-loading-icon text="响应中，请稍后..." textSize="16" :show="true"></u-loading-icon>
			</view>
			
			<!-- 超时错误提示 -->
			<view v-if="showTimeoutError" class="error_message">
				<text>服务器繁忙，请稍后重试</text>
			</view>
			
			<!-- 连接错误提示 -->
			<view v-if="showConnectionError" class="error_message">
				<text>连接失败，请稍后再试</text>
			</view>
		</view>
		
		<!-- 底部输入区域 -->
		<view class="input_tab">
			<!-- 服务说明 - 移到输入框上方 -->
			<view class="statement">智能家居服务<text @tap="exemptStatement">使用说明</text></view>
			
			<!-- 输入组件区域 -->
			<view class="input_com">
				<!-- 左侧输入区域 -->
				<view class="left">
					<!-- 发送图标 -->
					<image src="../../static/icon/send.png"></image>
					<!-- 输入框，绑定userQuesion变量，设置占位符和光标间距 -->
					<input placeholder="请输入问题" v-model.trim="userQuesion" cursor-spacing="30rpx"></input>
				</view>
				<!-- 发送按钮，点击触发sendMsg方法，移除右边距使其紧贴输入框 -->
				<view class="send_btn" @tap="sendMsg">发送</view>
			</view>
		</view>
	</view>
</template>

<script>
	// 导入位于相对路径"../../components/statement.vue"的statement组件
	import statement from "../../components/statement.vue";
	// 从marked库中导入marked函数，用于将Markdown文本转换为HTML
	import { marked } from "marked";
	// 导出一个Vue组件对象
	export default {
		// 注册导入的statement组件，使其可在模板中使用
		components: {
			statement
		},
		// 定义组件的数据对象
		data() {
			// 开始返回数据对象
			return {
				// 用户头像图片URL，初始为空字符串
				userImg: '',
				// 默认用户头像图片路径
				nullImg: '../../static/icon/user.png',
				// 控制是否显示加载状态的标志位
				showLoading: false,
				// 预设的问题请求数组
				postRequest: [
					{ id: 1, text: '把空调温度调低一点' },
					{ id: 2, text: '打开卧室灯' },
					{ id: 3, text: '显示当前气温' }
				],
				// 存储聊天记录的数组
				chatList: [],
				// 存储用户输入的问题
				userQuesion: '',
				// 存储机器人的回答
				robotAnswer: '',
				// 存储当前时间
				currentDate: '',
				// 存储DOM元素的高度
				domHeight: 0,
				// 初始化与AI对话的消息数组，第一条为系统角色设定消息
				messages: [
					{
						role: "system",
						content: "你是一名专业的智能家居助手，专注于帮助用户控制家居设备（如灯光、空调、热水器）、查询设备状态和执行场景模式。当用户询问与智能家居无关的问题时，礼貌拒绝并引导至相关功能。"
					}
				],
				// 超时定时器ID
				timeoutTimer: null,
				// 响应超时时间（毫秒），默认30秒
				responseTimeout: 30000,
				// 是否显示超时错误信息
				showTimeoutError: false,
				// 是否显示连接错误信息
				showConnectionError: false,
				// WebSocket实例
				socketTask: null,
				// 连接状态
				connected: false,
				// 聊天历史记录
				history: []
			};
		},
		// 页面加载生命周期函数
		onLoad(option) {
			// 如果没有传入questionText参数则直接返回
			if (!option.questionText) return;
			this.userQuesion = option.questionText;
			// 将传入的参数questionText赋值给userQuesion
			this.sendMsg();
		},
		// 定义侦听器
		watch: {
			// 监听chatList数组长度的变化
			'chatList.length': {
				// 立即执行且深度监听
				immediate: true,
				deep: true,
				// 定义处理函数
				handler(newValue, oldValue) {
					// 当chatList长度变化时，自动滚动到底部
					if (newValue) {
						this.scrollToBottom();
					}
				}
			},
			// 监听chatList内容变化（用于流式更新时的滚动）
			chatList: {
				deep: true,
				handler(newList, oldList) {
					// 当消息内容更新时，延迟滚动确保DOM已更新
					this.$nextTick(() => {
						this.scrollToBottom();
					});
				}
			}
		},
		// 组件挂载完成生命周期函数
		mounted() { 
			// 通过refs打开居中显示的dialog组件
			this.$refs.dialog.open('center');
			// 获取当前时间并格式化为HH:MM格式
			let myDate = new Date();
			this.currentDate = (myDate.getHours() + '').padStart(2, '0') + ':' + (myDate.getMinutes() + '').padStart(2, '0');
			// 初始化WebSocket连接
			this.initSocket();
			
			// 初始滚动到底部
			this.$nextTick(() => {
				this.scrollToBottom();
			});
		},
		// 页面卸载前关闭WebSocket连接
		beforeUnmount() {
			if (this.socketTask) {
				this.socketTask.close();
			}
		},
		// 定义组件方法
		methods: {
			// 自动滚动到页面底部 - 修改为适配绝对定位的聊天区域
			scrollToBottom() {
				this.$nextTick(() => {
					// 获取聊天区域DOM元素并滚动到底部
					const query = uni.createSelectorQuery().in(this);
					query.select('.chat_area').boundingClientRect().exec((res) => {
						if (res[0]) {
							// 使用scrollIntoView滚动到聊天区域底部
							setTimeout(() => {
								try {
									const chatArea = document.querySelector('.chat_area');
									if (chatArea) {
										chatArea.scrollTop = chatArea.scrollHeight;
									}
								} catch (e) {
									// 非web环境的兼容处理
									uni.createSelectorQuery()
										.select('.chat_area')
										.scrollOffset()
										.exec((res) => {
											if (res[0]) {
												const scrollTop = res[0].scrollHeight - res[0].clientHeight;
												if (scrollTop > 0) {
													// 使用uni.pageScrollTo在非web环境中滚动
													uni.pageScrollTo({
														scrollTop: scrollTop,
														duration: 300,
														selector: '.chat_area'
													});
												}
											}
										});
								}
							}, 100);
						}
					});
				});
			},
			
			htmlContent(content) { //转换为markdown 格式显示
				return marked(content);
			},
			// 打开使用说明对话框
			exemptStatement() {
				this.$refs.dialog.open('center');
			},
			// 点击预设问题时调用，发送对应文本
			tapQuestion(item) {
				this.wssend(item.text); // 修改为调用正确的websocket发送方法
			},
			
			// ----- 使用websocket方法
			// 建立 WebSocket 连接
			initSocket() {
				if (this.socketTask) return;

				this.socketTask = uni.connectSocket({
					url: "ws://127.0.0.1:8000/api/v1/ai/ws/chat",  // 改成你的后端地址
					success: () => {
						console.log("WebSocket 初始化成功");
					}
				});

				this.socketTask.onOpen(() => {
					this.connected = true;
					console.log("WebSocket 已连接");
				});

				this.socketTask.onMessage((res) => {
					try {
						const data = JSON.parse(res.data);
						if (data.token) {
							// 流式追加 token
							let lastIndex = this.chatList.length - 1;
							if (lastIndex >= 0 && this.chatList[lastIndex].role === 'assistant') {
								this.chatList[lastIndex].content += data.token;
							}
							// 收到回复后清除超时定时器和错误状态
							this.clearResponseTimeout();
							this.showConnectionError = false; // 清除连接错误状态
							
							// 流式更新时自动滚动
							this.$nextTick(() => {
								this.scrollToBottom();
							});
						} else if (data.event === "DONE") {
							// 一条完整回答结束，隐藏加载状态和清除超时
							this.showLoading = false;
							this.showTimeoutError = false;
							this.showConnectionError = false; // 清除连接错误状态
							this.clearResponseTimeout();
							let lastIndex = this.chatList.length - 1;
							if (lastIndex >= 0) {
								this.chatList[lastIndex].done = true;
							}
							// 消息完成时确保滚动到底部
							this.scrollToBottom();
						}
					} catch (e) {
						console.error("消息解析失败:", e, res.data);
					}
				});

				this.socketTask.onClose(() => {
					this.connected = false;
					console.log("WebSocket 已关闭");
				});

				this.socketTask.onError((err) => {
					console.error("WebSocket 出错:", err);
					// WebSocket出错时，立即终止"响应中"状态，显示连接错误信息
					this.showLoading = false;
					this.showConnectionError = true;
					this.clearResponseTimeout();
					
					// 3秒后自动隐藏错误信息
					setTimeout(() => {
						this.showConnectionError = false;
					}, 3000);
				});
			},

			// 清除响应超时定时器
			clearResponseTimeout() {
				if (this.timeoutTimer) {
					clearTimeout(this.timeoutTimer);
					this.timeoutTimer = null;
				}
			},
			
			// 设置响应超时定时器
			setResponseTimeout() {
				this.clearResponseTimeout(); // 先清除之前的定时器
				this.timeoutTimer = setTimeout(() => {
					// 超时后隐藏加载状态，显示错误信息
					this.showLoading = false;
					this.showTimeoutError = true;
					console.log('服务器响应超时');
					
					// 滚动确保超时错误信息可见
					this.$nextTick(() => {
						this.scrollToBottom();
					});
					
					// 3秒后自动隐藏错误信息
					setTimeout(() => {
						this.showTimeoutError = false;
					}, 3000);
				}, this.responseTimeout);
			},

			// 发送用户输入
			async wssend(val) {
				if (!this.connected) {
					this.initSocket();
					await new Promise(resolve => setTimeout(resolve, 500)); // 等待连接
				}

				// 打印当前消息数组并显示加载状态
				console.log(this.messages);
				
				this.showLoading = true;
				this.showTimeoutError = false; // 重置错误状态
				this.showConnectionError = false; // 重置连接错误状态
				
				// 设置响应超时定时器
				this.setResponseTimeout();
				// 创建用户消息对象并添加到聊天列表和消息数组
				let userMessage = {
					role: 'user',
					content: val
				};
				this.chatList.push(userMessage);
				this.messages.push(userMessage);

				// 创建空的助手消息对象并添加到两个数组
				let assistantMessage = {
					role: 'assistant',
					content: ''
				};
				this.chatList.push(assistantMessage);
				this.messages.push(assistantMessage);

				// 立即滚动到底部显示用户消息和"响应中"状态
				this.$nextTick(() => {
					this.scrollToBottom();
				});

				this.socketTask.send({
					data: JSON.stringify({
						message: val,
						history: this.history
					})
				});

				// 把用户输入追加到 history 里
				this.history.push({ role: "user", content: val });
				this.history.push({ role: "assistant", content: "" }); // 等模型返回后填充
			},
			
			// 发送用户问题并清空输入
			sendMsg() {
				if (!this.userQuesion.trim()) {
					uni.showToast({
						title: '请输入问题',
						icon: 'none'
					});
					return;
				}
				// 调用websocket方法
				this.wssend(this.userQuesion);
				this.userQuesion = '';
				this.robotAnswer = '';
				
				// 发送消息后滚动到底部
				this.$nextTick(() => {
					this.scrollToBottom();
				});
			}
		}
	};
</script>

<style lang="scss" scoped>
	// 容器样式 - 使用绝对定位避免滚动问题
	.container {
		position: fixed;
		top: 0;
		left: 0;
		width: 100vw;
		height: 100vh;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	// 背景图片 - 固定背景，不随页面滚动
	.bg {
		position: fixed;
		width: 100vw;
		height: 100vh;
		object-fit: cover;
		object-position: center;
		z-index: 1;
		top: 0;
		left: 0;
	}

	// 遮罩层 - 固定遮罩
	.overlay {
		position: fixed;
		width: 100vw;
		height: 100vh;
		background: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.6));
		z-index: 2;
		top: 0;
		left: 0;
	}

	// 聊天区域样式 - 修改为绝对定位，底部距离280rpx
	.chat_area {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 220rpx; // 设置底部距离为280rpx
		z-index: 3;
		padding: 40rpx 28rpx 40rpx 28rpx; // 调整底部padding，避免内容贴边
		overflow-y: auto;
		overflow-x: hidden; // 防止横向滚动
		
		// 滚动条样式优化（仅在支持的浏览器中生效）
		&::-webkit-scrollbar {
			width: 4rpx;
		}
		
		&::-webkit-scrollbar-track {
			background: rgba(255, 255, 255, 0.1);
			border-radius: 2rpx;
		}
		
		&::-webkit-scrollbar-thumb {
			background: rgba(255, 255, 255, 0.3);
			border-radius: 2rpx;
		}
		
		&::-webkit-scrollbar-thumb:hover {
			background: rgba(255, 255, 255, 0.5);
		}
		
		// 当前时间显示样式
		.current_time {
			display: flex;
			justify-content: center;
			font-size: 12px;
			color: rgba(255, 255, 255, 0.8);
			margin: 20rpx 0;
		}

		// 左侧和右侧消息框的共同样式
		.left_box,
		.right_box {
			display: flex;
			margin: 20rpx 16rpx;

			// 消息内容框样式 - 使用毛玻璃效果
			.content_box {
				max-width: 80%;
				min-width: 80rpx;
				width: fit-content;
				word-wrap: break-word;
				overflow-wrap: break-word;

				.content {
					padding: 32rpx 40rpx;
					border-radius: 30rpx;
					box-shadow: 0 15rpx 40rpx rgba(0, 0, 0, 0.2);
					backdrop-filter: blur(20rpx);
					
					// 字体样式调整
					font-size: 16px !important;
					font-weight: 540 !important;
					line-height: 24px !important;
					-webkit-text-size-adjust: none !important;
					text-size-adjust: none !important;
					zoom: 1 !important;
					transform: none !important;
					margin: 0;

					// 请求帖子样式 - 去除示例问题的背景
					.post_request {
						color: #666666;
						display: flex;
						flex-direction: column;
						margin: 0;
						
						view {
							margin: 6rpx 0;
							padding: 12rpx 20rpx;
							border-radius: 16rpx;
							background: transparent;
							
							.active {
								color: #007AFF;
								cursor: pointer;
								font-weight: 540 !important;
								line-height: 24px !important;
								
								&:hover {
									background-color: rgba(0, 122, 255, 0.1);
								}
								
								&:active {
									background-color: rgba(0, 122, 255, 0.2);
									opacity: 0.8;
								}
							}
						}
					}
				    
				    // 强制所有HTML内容元素使用统一的字体样式
				    *, p, div, span, text, view {
				    	font-size: 16px !important;
				    	line-height: 24px !important;
				    	font-weight: 540 !important;
				    	-webkit-text-size-adjust: none !important;
				    	text-size-adjust: none !important;
				    	zoom: 1 !important;
				    	transform: none !important;
				    	margin: 0 !important;
				    }
				    
				    h1, h2, h3, h4, h5, h6 {
				    	font-size: 16px !important;
				    	line-height: 24px !important;
				    	font-weight: 540 !important;
				    	margin: 0 !important;
				    }
				    
				    li, ul, ol {
				    	font-size: 16px !important;
				    	line-height: 24px !important;
				    	font-weight: 540 !important;
				    	margin: 0 !important;
				    }
				    
				    strong, b {
				    	font-size: 16px !important;
				    	line-height: 24px !important;
				    	font-weight: 540 !important;
				    }
				    
				    em, i {
				    	font-size: 16px !important;
				    	line-height: 24px !important;
				    	font-weight: 540 !important;
				    	font-style: normal !important;
				    }
				    
				    code, pre {
				    	font-size: 16px !important;
				    	line-height: 24px !important;
				    	font-weight: 540 !important;
				    	font-family: inherit !important;
				    }
				}
			}
		}
		
		// 左侧消息框（机器人） - 使用更清亮的毛玻璃效果
		.left_box {
			justify-content: flex-start;
			
			.content_box {
				background: rgba(255, 255, 255, 0.85) !important;
				color: #333333 !important;
				border-radius: 44rpx 44rpx 44rpx 8rpx !important;
				border: 1rpx solid rgba(255, 255, 255, 0.5);
				backdrop-filter: blur(15rpx);
			}
		}
		
		// 右侧消息框（用户） - 仿照机器人对话框调整
		.right_box {
			justify-content: flex-end;
			
			.content_box {
				background: linear-gradient(180deg, #4A9EFF 0%, #7BB8FF 100%) !important;
				color: #ffffff !important;
				margin-left: auto;
				border-radius: 44rpx 44rpx 8rpx 44rpx !important;
				border: 1rpx solid rgba(255, 255, 255, 0.5);
				backdrop-filter: blur(15rpx);
				
				.content {
					color: #ffffff !important;
					
					*, p, div, span, text, view {
						color: #ffffff !important;
					}
				}
			}
		}
	}

	// 加载提示容器样式
	.loading-container {
		display: flex;
		justify-content: center;
		align-items: center;
		padding: 20rpx 0;
		margin: 20rpx 0;
		flex-shrink: 0; // 防止被压缩
	}

	// 错误信息提示样式 - 确保在聊天区域内显示
	.error_message {
		display: flex;
		justify-content: center;
		align-items: center;
		padding: 20rpx;
		margin: 20rpx 0; // 改为上下边距，避免左右边距影响布局
		background: rgba(255, 242, 240, 0.9);
		border: 1rpx solid rgba(255, 204, 199, 0.8);
		border-radius: 16rpx;
		backdrop-filter: blur(10rpx);
		max-width: 100%; // 确保不超出聊天区域
		box-sizing: border-box;
		flex-shrink: 0; // 防止被压缩
		
		text {
			color: #ff4d4f;
			font-size: 14px;
			text-align: center;
		}
	}

	// 底部输入栏样式 - 调整布局顺序
	.input_tab {
		position: absolute;
		bottom: 80rpx;
		left: 0;
		right: 0;
		height: 240rpx;
		z-index: 10;
		background: transparent;
		display: flex;
		flex-direction: column;
		justify-content: flex-end; // 改为底部对齐
		padding: 20rpx 0;
		box-sizing: border-box;
	}

	// 声明文字样式 - 调整边距，现在在输入框上方
	.statement {
		margin: 0 auto 0rpx auto; // 调整边距，底部留给输入框空间
		font-size: 12px;
		color: rgba(255, 255, 255, 0.8);
		text-align: center;

		text {
			color: #FFFFFF;
			text-decoration: underline;
			font-weight: 500;
		}
	}
	
	// 输入组件容器样式
	.input_com {
		display: flex;
		justify-content: space-between;
		padding: 16rpx 30rpx;
		gap: 16rpx;

		// 左侧输入区域样式 - 使用毛玻璃效果
		.left {
			flex: 1;
			border: 2rpx solid rgba(255, 255, 255, 0.3);
			display: flex;
			align-items: center;
			background: rgba(255, 255, 255, 0.15);
			backdrop-filter: blur(10rpx);
			border-radius: 48rpx;
			padding: 0 8rpx;
			min-height: 80rpx;

			// 输入框内图标样式
			image {
				width: 32rpx;
				height: 32rpx;
				margin: 0 24rpx;
				opacity: 0.8;
			}
			
			// 输入框样式
			input {
				width: 100%;
				font-size: 16px;
				background-color: transparent;
				border: none;
				outline: none;
				padding: 20rpx 0;
				color: #FFFFFF;
				
				&::placeholder {
					color: rgba(255, 255, 255, 0.7);
				}
			}
		}
		
		// 发送按钮样式
		.send_btn {
			width: 80rpx;
			height: 80rpx;
			padding: 0;
			color: #ffffff;
			border-radius: 40rpx;
			background: linear-gradient(180deg, #4A9EFF 0%, #7BB8FF 100%);
			border: none;
			flex-shrink: 0;
			display: flex;
			align-items: center;
			justify-content: center;
			font-size: 14px;
			font-weight: 500;
			box-shadow: 0 15rpx 40rpx rgba(0, 0, 0, 0.2);
			
			&:active {
				transform: scale(0.95);
				opacity: 0.8;
			}
		}
	}
</style>