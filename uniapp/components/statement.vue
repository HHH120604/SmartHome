<!-- 定义Vue模板部分 -->
<template>
	<!-- 自定义模态框容器 -->
	<view v-if="show" class="modal-overlay" @click="handleOverlayTap">
		<view class="modal-container" @click.stop>
			<!-- 模态框标题 -->
			<view class="modal-header">
				<text class="modal-title">{{ title }}</text>
			</view>
			
			<!-- 模态框内容 -->
			<view class="modal-content">
				<text class="content-text">{{ content }}</text>
			</view>
			
			<!-- 模态框按钮 -->
			<view class="modal-buttons">
				<button class="btn-cancel" @click="cancel">取消</button>
				<button class="btn-confirm" @click="confirm">确认</button>
			</view>
		</view>
	</view>
</template>

<!-- 定义组件逻辑 -->
<script>
	// 导出Vue组件
	export default {
		// 组件名称为"statement"
		name: "statement",
		// 组件数据定义
		data() {
			// 返回数据对象
			return {
				// 控制模态框显示/隐藏的标志
				show: false,
				// 模态框标题
				title: "使用说明",
				// 模态框内容，使用模板字符串定义多行文本
				content: `1.本助手专注于智能家居基础服务，包括控制已添加的智能设备、查看屋内实时气温与湿度、监测可燃气体浓度等，不提供除此之外的其他信息或功能。

2.如遇到火灾、燃气泄漏、入侵等紧急情况，请立即按照相关安全预案处理，并联系专业紧急服务部门。

3.请勿提出与智能家居控制及监测无关的问题，本助手无法予以回应。

4.您在使用本服务过程中产生的任何个人信息与家庭数据，我们将依照隐私政策予以严格保护。`
			};
		},
		// 组件方法定义
		methods: {
			// 打开模态框的方法，position参数默认为'center'
			open(position = 'center') {
				// 设置show为true以显示模态框
				this.show = true;
			},
			// 确认按钮点击事件处理
			confirm() {
				// 隐藏模态框
				this.show = false;
				// 触发确认事件
				this.$emit('confirm');
			},
			// 取消按钮点击事件处理
			cancel() {
				// 隐藏模态框
				this.show = false;
				// 触发取消事件
				this.$emit('cancel');
			},
			// 关闭模态框事件处理
			close() {
				// 隐藏模态框
				this.show = false;
				// 触发关闭事件
				this.$emit('close');
			},
			// 处理遮罩层点击事件
			handleOverlayTap() {
				// 点击遮罩层关闭模态框
				this.close();
			}
		}
	};
</script>

<!-- 组件样式部分 -->
<style scoped lang="scss">
	// 模态框遮罩层
	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: rgba(0, 0, 0, 0.6);
		backdrop-filter: blur(10rpx);
		display: flex;
		justify-content: center;
		align-items: center;
		z-index: 9999;
		padding: 40rpx;
		box-sizing: border-box;
	}

	// 模态框容器 - 改用更清亮的背景，去除边角阴影
	.modal-container {
		width: 100%;
		max-width: 600rpx;
		background: rgba(255, 255, 255, 0.98);
		backdrop-filter: blur(25rpx);
		border-radius: 30rpx;
		box-shadow: 0 20rpx 60rpx rgba(0, 0, 0, 0.15);
		border: 1rpx solid rgba(255, 255, 255, 0.8);
		overflow: hidden;
		animation: modalShow 0.3s ease-out;
	}

	// 模态框动画
	@keyframes modalShow {
		from {
			opacity: 0;
			transform: scale(0.8) translateY(50rpx);
		}
		to {
			opacity: 1;
			transform: scale(1) translateY(0);
		}
	}

	// 模态框头部
	.modal-header {
		padding: 50rpx 40rpx 30rpx 40rpx;
		text-align: center;
		border-bottom: 1rpx solid rgba(0, 0, 0, 0.05);
	}

	// 模态框标题
	.modal-title {
		font-size: 36rpx;
		font-weight: bold;
		color: #007AFF;
		letter-spacing: 2rpx;
	}

	// 模态框内容区域
	.modal-content {
		padding: 40rpx;
		max-height: 60vh;
		overflow-y: auto;
	}

	// 内容文字
	.content-text {
		font-size: 28rpx;
		line-height: 44rpx;
		color: #333;
		text-align: left;
		white-space: pre-line;
		word-wrap: break-word;
	}

	// 按钮容器
	.modal-buttons {
		display: flex;
		border-top: 1rpx solid rgba(0, 0, 0, 0.05);
	}

	// 按钮基础样式
	.btn-cancel,
	.btn-confirm {
		flex: 1;
		height: 96rpx;
		line-height: 96rpx;
		text-align: center;
		font-size: 32rpx;
		font-weight: 500;
		border: none;
		background: transparent;
		transition: all 0.3s ease;
		border-radius: 0;
		
		&:active {
			transform: scale(0.98);
		}
	}

	// 取消按钮
	.btn-cancel {
		color: #666;
		border-right: 1rpx solid rgba(0, 0, 0, 0.05);
		
		&:hover {
			background: rgba(0, 0, 0, 0.02);
		}
	}

	// 确认按钮
	.btn-confirm {
		color: #007AFF;
		font-weight: 600;
		
		&:hover {
			background: rgba(0, 122, 255, 0.05);
		}
	}

	// 滚动条样式优化
	.modal-content::-webkit-scrollbar {
		width: 6rpx;
	}

	.modal-content::-webkit-scrollbar-thumb {
		background-color: rgba(0, 0, 0, 0.1);
		border-radius: 3rpx;
	}

	.modal-content::-webkit-scrollbar-track {
		background-color: transparent;
	}
</style>