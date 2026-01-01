<template>
  <div class="introview-container" :style="{ '--fade-ms': fadeMs + 'ms' }">
    <!-- 背景：两层叠加做淡入淡出 -->
    <div class="bg-layer bg-front" :style="{ backgroundImage: `url('${bgFront}')` }"></div>
    <div
      class="bg-layer bg-back"
      :class="{ 'is-fading': isFading }"
      :style="{ backgroundImage: `url('${bgBack}')` }"
    ></div>

    <!-- 统一遮罩：让前景内容更清晰 -->
    <div class="bg-overlay"></div>

    <div class="page-inner">
      <div class="page-title">
        <h1 class="h3 m-0">项目简介</h1>
        <div class="subtitle">周杰伦歌曲关系知识图谱 · 课设展示</div>
      </div>

      <div class="content-card">
        <div class="content">
          <p>
            <strong>周杰伦（Jay Chou）</strong>
            ，1979年1月18日出生于台湾省，祖籍福建省泉州市永春县，中国台湾流行乐男歌手、音乐人、演员、导演、编剧……出道至今已发布多张专辑，数百首歌曲，《七里香》、《听妈妈的话》、《青花瓷》等耳熟能详的歌曲陪伴一代又一代人的青春岁月。
          </p>
          <p>
            本项目尝试对周杰伦出道以来参与过的所有歌曲作品、专辑以及合作歌手、作词人进行关系分析，将这些信息组织成三元组构建知识图谱，并基于知识图谱实现一个有关周杰伦歌曲的在线检索系统。
          </p>
          <p>
            我们首先利用爬虫技术爬取有关周杰伦歌曲信息的文本描述，利用知识图谱抽取工具 DeepKE 抽取文本描述中的实体和关系，并使用 Neo4j 搭建知识图谱。最后，我们基于 Python 的轻量级后端开发框架 Flask 和前端框架 Vue 实现了一个基于知识图谱的在线检索系统。
          </p>
        </div>

        <!-- 轮播指示点（可点击跳转） -->
        <div class="dots">
          <span
            v-for="(img, idx) in images"
            :key="img"
            class="dot"
            :class="{ active: idx === index }"
            @click="goTo(idx)"
            :title="`第 ${idx + 1} 张`"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "IntroView",
  data() {
    return {
      base:
        (import.meta && import.meta.env && import.meta.env.BASE_URL)
          ? import.meta.env.BASE_URL
          : "/",

      folder: "image", // 你的目录：public/image

      images: [],
      index: 0,

      // 轮播速度（想更快就继续减小）
      intervalMs: 2500,

      // 淡入淡出时间（会同步到 CSS）
      fadeMs: 500,

      timer: null,

      bgFront: "",
      bgBack: "",
      isFading: false,
      fadeTimer: null,
    };
  },

  mounted() {
    this.images = Array.from({ length: 10 }, (_, i) => this.buildUrl(i + 1));

    // 预加载，减少某几张切换时卡顿感
    this.preload(this.images);

    this.bgFront = this.images[0] || "";
    this.bgBack = this.images[1] || this.images[0] || "";

    this.start();
  },

  beforeUnmount() {
    this.stop();
  },

  methods: {
    buildUrl(n) {
      const base = this.base.endsWith("/") ? this.base : this.base + "/";
      return `${base}${this.folder}/${n}.jpg`; // /image/1.jpg ...
    },

    preload(urls) {
      try {
        urls.forEach((u) => {
          const img = new Image();
          img.src = u;
        });
      } catch (e) {}
    },

    start() {
      this.stop();
      this.timer = setInterval(() => {
        this.next();
      }, this.intervalMs);
    },

    stop() {
      if (this.timer) {
        clearInterval(this.timer);
        this.timer = null;
      }
      if (this.fadeTimer) {
        clearTimeout(this.fadeTimer);
        this.fadeTimer = null;
      }
      this.isFading = false;
    },

    next() {
      const nextIndex = (this.index + 1) % this.images.length;
      this.transitionTo(nextIndex);
    },

    goTo(i) {
      if (i === this.index) return;
      this.transitionTo(i);
    },

    transitionTo(nextIndex) {
      // 防止淡入淡出重叠（不会丢整轮，因为 intervalMs 远大于 fadeMs）
      if (this.isFading) return;

      this.bgBack = this.images[nextIndex];
      this.isFading = true;

      this.fadeTimer = setTimeout(() => {
        this.bgFront = this.bgBack;
        this.index = nextIndex;
        this.isFading = false;
        this.fadeTimer = null;
      }, this.fadeMs);
    },
  },
};
</script>

<style lang="less" scoped>
.introview-container {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  background: #0b1b3a;
}

/* 背景图层 */
.bg-layer {
  position: absolute;
  inset: 0;
  background-repeat: no-repeat;

  /* 后者：铺满屏幕（会裁切） */
  background-size: cover;
  background-position: center 22%;

  /* 动一点：不那么僵硬 */
  animation: kenburns 10s ease-in-out infinite alternate;
  will-change: transform, opacity;
}

.bg-front {
  z-index: 0;
  opacity: 1;
}

.bg-back {
  z-index: 1;
  opacity: 0;
  transition: opacity var(--fade-ms) ease; /* ✅ 自动同步 */
}
.bg-back.is-fading {
  opacity: 1;
}

/* 统一遮罩：压暗+柔光 */
.bg-overlay {
  position: absolute;
  inset: 0;
  z-index: 2;
  background:
    radial-gradient(1200px 700px at 20% 10%, rgba(0,0,0,0.18), rgba(0,0,0,0) 60%),
    linear-gradient(120deg, rgba(0,0,0,0.62), rgba(0,0,0,0.28));
}

.page-inner {
  position: relative;
  z-index: 3;
  padding: 22px 26px 50px;
}

.page-title {
  color: #fff;
  padding: 8px 6px 18px;
}
.subtitle {
  margin-top: 6px;
  font-size: 13px;
  opacity: 0.85;
}

.content-card {
  max-width: 980px;
  margin: 54px auto 0;
  border-radius: 18px;
  padding: 20px 22px 12px;

  background: rgba(255, 255, 255, 0.78);
  -webkit-backdrop-filter: blur(10px) saturate(120%);
  backdrop-filter: blur(10px) saturate(120%);

  border: 1px solid rgba(255, 255, 255, 0.26);
  box-shadow: 0 18px 44px rgba(0, 0, 0, 0.22);
}

.content {
  width: 92%;
  margin-left: 8px;
  text-indent: 2rem;
  line-height: 1.9;
  color: #111;
}

.dots {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
  padding: 10px 4px 2px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.25);
  cursor: pointer;
  transition: transform 120ms ease, background 120ms ease;
}
.dot:hover { transform: scale(1.25); }
.dot.active { background: rgba(0, 0, 0, 0.75); }

@keyframes kenburns {
  from { transform: scale(1.03); }
  to   { transform: scale(1.07); }
}

@media (max-width: 768px) {
  .page-inner { padding: 18px 14px 40px; }
  .content-card { margin-top: 26px; padding: 16px 16px 10px; }
  .content { width: 100%; margin-left: 0; }
}
</style>
