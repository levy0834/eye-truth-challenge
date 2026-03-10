// 眼力试炼：真假识破 - 游戏核心逻辑

const GAME_CONFIG = {
  totalCredits: 10,
  roundDuration: 3000, // ms
  bonusThreshold: 1500, // ms
  points: {
    correct: 100,
    speedBonus: 50,
    wrong: -50
  },
  rounds: [
    { count: 5, time: 3000, mode: 'diff' }, // R1-5: 找不同（假图有明显改动）
    { count: 5, time: 3000, mode: 'same' }, // R6-10: 找相同（真图有细微差别）
    { count: 5, time: 2000, mode: 'mixed' } // R11-15: 混合 + 时间缩短
  ]
};

// 图形库：每个关卡的基础图形描述
const SHAPES = [
  { type: 'circle', color: '#ff6b6b', bg: '#1a1c2c' },
  { type: 'rect', color: '#ffd93d', bg: '#0a0e17' },
  { type: 'triangle', color: '#6bcb77', bg: '#1a1c2c' },
  { type: 'circle', color: '#4d96ff', bg: '#0a0e17' },
  { type: 'pentagon', color: '#ff6b9d', bg: '#1a1c2c' },
  { type: 'star', color: '#c9b1ff', bg: '#0a0e17' },
  { type: 'ellipse', color: '#ff9f43', bg: '#1a1c2c' },
  { type: 'hexagon', color: '#1dd1a1', bg: '#0a0e17' },
  { type: 'cross', color: '#ff6b6b', bg: '#1a1c2c' },
  { type: 'diamond', color: '#54a0ff', bg: '#0a0e17' }
];

class Game {
  constructor() {
    this.credits = GAME_CONFIG.totalCredits;
    this.score = 0;
    this.currentRound = 0;
    this.totalRounds = 15;
    this.correctAnswers = 0;
    this.roundTimes = [];
    this.currentStartTime = 0;
    this.timerInterval = null;
    this.selectedAnswer = null;

    this.canvasLeft = document.getElementById('canvas-left');
    this.canvasRight = document.getElementById('canvas-right');
    this.ctxLeft = this.canvasLeft.getContext('2d');
    this.ctxRight = this.canvasRight.getContext('2d');

    this.bindEvents();
  }

  bindEvents() {
    document.getElementById('start-btn').onclick = () => this.startGame();
    document.getElementById('img-left').onclick = () => this.answer('left');
    document.getElementById('img-right').onclick = () => this.answer('right');
    document.getElementById('restart-btn').onclick = () => this.restart();
    document.getElementById('copy-btn').onclick = () => this.copyShare();
  }

  startGame() {
    this.credits = GAME_CONFIG.totalCredits;
    this.score = 0;
    this.currentRound = 0;
    this.correctAnswers = 0;
    this.roundTimes = [];
    this.showScreen('game-screen');
    this.nextRound();
  }

  nextRound() {
    if (this.credits <= 0 || this.currentRound >= this.totalRounds) {
      this.endGame();
      return;
    }
    this.currentRound++;
    this.credits--;
    this.selectedAnswer = null;
    this.updateHud();

    // 计算当前回合的配置
    let roundConfig;
    let accumulated = 0;
    for (const r of GAME_CONFIG.rounds) {
      if (this.currentRound <= accumulated + r.count) {
        roundConfig = r;
        break;
      }
      accumulated += r.count;
    }

    // 生成题目
    this.generateRound(roundConfig);
  }

  generateRound(config) {
    const shapeIndex = (this.currentRound - 1) % SHAPES.length;
    const baseShape = SHAPES[shapeIndex];

    // 决定哪边是假图（true=left假，false=right假）
    this.fakeSide = Math.random() < 0.5 ? 'left' : 'right';

    // 根据模式决定改动幅度
    let diffIntensity;
    if (config.mode === 'diff') {
      diffIntensity = 0.5; // 明显改动
      document.getElementById('question-text').innerHTML = '哪张图是<span class="highlight">假的</span>？';
    } else if (config.mode === 'same') {
      diffIntensity = 0.2; // 细微差别
      document.getElementById('question-text').innerHTML = '哪张图是<span class="highlight">真</span>的？';
      this.fakeSide = this.fakeSide === 'left' ? 'right' : 'left'; // 反转：玩家要找真图
    } else {
      diffIntensity = Math.random() < 0.5 ? 0.4 : 0.2;
      document.getElementById('question-text').innerHTML = '哪张图是<span class="highlight">假的</span>？';
    }

    // 生成两个画布内容
    this.drawCanvas(this.ctxLeft, this.canvasLeft, baseShape, this.fakeSide === 'left', diffIntensity);
    this.drawCanvas(this.ctxRight, this.canvasRight, baseShape, this.fakeSide === 'right', diffIntensity);

    // 启动倒计时
    this.startTimer(config.time);
  }

  drawCanvas(ctx, canvas, baseShape, isFake, intensity) {
    const w = canvas.width;
    const h = canvas.height;
    const bg = baseShape.bg;
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, w, h);

    // 基础图形
    this.drawShape(ctx, w/2, h/2, 100, baseShape.type, baseShape.color);

    if (isFake) {
      // 假图：添加改动
      const changes = [
        () => {
          // 颜色微调
          const color = this.adjustColor(baseShape.color, intensity);
          ctx.fillStyle = color;
          this.drawShape(ctx, w/2, h/2, 100, baseShape.type, color, true);
        },
        () => {
          // 位置偏移
          ctx.save();
          ctx.translate(w*0.15, h*0.15);
          this.drawShape(ctx, w/2, h/2, 100, baseShape.type, baseShape.color, true);
          ctx.restore();
        },
        () => {
          // 大小变化
          const scale = 0.8 + intensity*0.4;
          ctx.save();
          ctx.translate(w/2, h/2);
          ctx.scale(scale, scale);
          this.drawShape(ctx, 0, 0, 100, baseShape.type, baseShape.color, true);
          ctx.restore();
        },
        () => {
          // 旋转
          ctx.save();
          ctx.translate(w/2, h/2);
          ctx.rotate(intensity * Math.PI/4);
          this.drawShape(ctx, 0, 0, 100, baseShape.type, baseShape.color, true);
          ctx.restore();
        },
        () => {
          // 叠加小元素
          ctx.fillStyle = this.adjustColor(baseShape.color, 0.5);
          this.drawShape(ctx, w/3, h/3, 40, 'circle', ctx.fillStyle);
        }
      ];
      const change = changes[Math.floor(Math.random() * changes.length)];
      change.call(ctx);
    }
  }

  drawShape(ctx, x, y, size, type, color, overlay = false) {
    ctx.fillStyle = color;
    ctx.beginPath();
    switch (type) {
      case 'circle':
        ctx.arc(x, y, size/2, 0, Math.PI*2);
        break;
      case 'rect':
        ctx.rect(x-size/2, y-size/2, size, size);
        break;
      case 'triangle':
        ctx.moveTo(x, y-size/2);
        ctx.lineTo(x+size/2, y+size/2);
        ctx.lineTo(x-size/2, y+size/2);
        break;
      case 'pentagon':
        this.drawPolygon(ctx, x, y, size/2, 5);
        break;
      case 'hexagon':
        this.drawPolygon(ctx, x, y, size/2, 6);
        break;
      case 'star':
        this.drawStar(ctx, x, y, size/2, size/4, 5);
        break;
      case 'ellipse':
        ctx.ellipse(x, y, size/2, size/3, 0, 0, Math.PI*2);
        break;
      case 'cross':
        const t = size/4;
        ctx.rect(x-t, y-size/2, t*2, size);
        ctx.rect(x-size/2, y-t, size, t*2);
        break;
      case 'diamond':
        ctx.moveTo(x, y-size/2);
        ctx.lineTo(x+size/2, y);
        ctx.lineTo(x, y+size/2);
        ctx.lineTo(x-size/2, y);
        break;
    }
    ctx.fill();
  }

  drawPolygon(ctx, x, y, r, sides) {
    for (let i = 0; i < sides; i++) {
      const angle = (i / sides) * Math.PI * 2 - Math.PI/2;
      const px = x + Math.cos(angle) * r;
      const py = y + Math.sin(angle) * r;
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.closePath();
  }

  drawStar(ctx, x, y, r1, r2, points) {
    for (let i = 0; i < points*2; i++) {
      const angle = (i / (points*2)) * Math.PI * 2 - Math.PI/2;
      const r = i % 2 === 0 ? r1 : r2;
      const px = x + Math.cos(angle) * r;
      const py = y + Math.sin(angle) * r;
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.closePath();
  }

  adjustColor(hex, factor) {
    // 简单颜色调整
    const r = parseInt(hex.slice(1,3), 16);
    const g = parseInt(hex.slice(3,5), 16);
    const b = parseInt(hex.slice(5,7), 16);
    const adjust = (c) => Math.min(255, Math.floor(c * (0.7 + factor*0.6)));
    const nr = adjust(r);
    const ng = adjust(g);
    const nb = adjust(b);
    return `rgb(${nr},${ng},${nb})`;
  }

  startTimer(duration) {
    this.currentStartTime = Date.now();
    const timerBar = document.getElementById('timer-progress');
    timerBar.style.transition = `width ${duration}ms linear`;
    timerBar.style.width = '0%';

    setTimeout(() => {
      this.timerEnd();
    }, duration);
  }

  timerEnd() {
    if (this.selectedAnswer === null) {
      this.handleAnswer(null, Date.now() - this.currentStartTime);
    }
  }

  answer(side) {
    if (this.selectedAnswer !== null) return; // 防止重复点击
    this.selectedAnswer = side;
    const timeUsed = Date.now() - this.currentStartTime;
    this.handleAnswer(side, timeUsed);
  }

  handleAnswer(side, time) {
    this.roundTimes.push(time);

    // 判定：找不同模式下，选fakeSide正确；找相同模式下，选!fakeSide正确
    let isCorrect = false;
    const isDiffMode = document.getElementById('question-text').innerText.includes('假的');
    if (side !== null) {
      if (isDiffMode) {
        isCorrect = side === this.fakeSide;
      } else {
        isCorrect = side !== this.fakeSide;
      }
    }

    // 计分
    if (isCorrect) {
      this.correctAnswers++;
      this.score += GAME_CONFIG.points.correct;
      if (time < GAME_CONFIG.bonusThreshold) {
        this.score += GAME_CONFIG.points.speedBonus;
      }
      this.showFeedback(`正确! +${GAME_CONFIG.points.correct}${time < GAME_CONFIG.bonusThreshold ? ' 速度+50' : ''}`, 'correct');
    } else if (side !== null) {
      this.score = Math.max(0, this.score + GAME_CONFIG.points.wrong);
      this.showFeedback(`错误 -50`, 'wrong');
    } else {
      this.showFeedback('时间到! -50', 'wrong');
      this.score = Math.max(0, this.score + GAME_CONFIG.points.wrong);
    }

    this.updateHud();
    setTimeout(() => this.nextRound(), 800);
  }

  showFeedback(text, type) {
    const fb = document.getElementById('feedback');
    fb.textContent = text;
    fb.className = 'feedback ' + type;
    setTimeout(() => fb.textContent = '', 700);
  }

  updateHud() {
    document.getElementById('credits').textContent = this.credits;
    document.getElementById('score').textContent = this.score;
    document.getElementById('round').textContent = `${this.currentRound}/${this.totalRounds}`;
  }

  endGame() {
    const accuracy = this.roundTimes.length > 0
      ? Math.round((this.correctAnswers / this.roundTimes.length) * 100)
      : 0;
    const avgTime = this.roundTimes.length > 0
      ? (this.roundTimes.reduce((a,b)=>a+b,0) / this.roundTimes.length / 1000).toFixed(1)
      : 0;

    // 称号
    let title = '眼力萌新';
    if (accuracy >= 90 && parseFloat(avgTime) < 1.0) title = '🔥 真相猎手';
    else if (accuracy >= 80) title = '👁️ 识破大师';
    else if (accuracy >= 60) title = '🔍 见习侦探';
    else if (accuracy >= 40) title = '😵 常被骗群众';
    else title = '🤡 谣言传播者';

    document.getElementById('final-score').textContent = this.score;
    document.getElementById('accuracy').textContent = accuracy + '%';
    document.getElementById('avg-time').textContent = avgTime;
    document.getElementById('title').textContent = title;

    // 分享文案
    const share = `我在「眼力试炼：真假识破」中得了 ${this.score} 分！\n正确率 ${accuracy}%，称号「${title}」\n你能超越我吗？`;
    document.getElementById('share-text').textContent = share;

    this.showScreen('result-screen');
  }

  restart() {
    this.startGame();
  }

  showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(id).classList.add('active');
  }

  copyShare() {
    const text = document.getElementById('share-text').textContent;
    navigator.clipboard.writeText(text).then(() => {
      const btn = document.getElementById('copy-btn');
      const orig = btn.textContent;
      btn.textContent = '已复制!';
      setTimeout(() => btn.textContent = orig, 1500);
    });
  }
}

// 启动
window.onload = () => {
  new Game();
};
