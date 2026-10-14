import { defineConfig } from 'vitepress'

// 内容仓浏览站：直接浏览 markdown 甲骨文库。
// 部署到 GitHub Pages 项目页（base /<repo>/）；不绑自定义域（分站才是 jiagu.diuci.com）。
const base = process.env.SITE_BASE || '/chinese-oracle-bone-script/'

export default defineConfig({
  base,
  lang: 'zh-CN',
  title: '甲骨文开源库',
  titleTemplate: ':title | 甲骨文开源库',
  description: '收录最完整、字形可核验的开源甲骨文内容库。商代公版卜辞，字源解说 CC BY 4.0，按字类/难度/今字分门别类。',

  themeConfig: {
    nav: [
      { text: '总览', link: '/' },
      { text: '索引', link: '/characters/索引' },
      { text: '打印版', link: '/print' },
      { text: '数据来源', link: '/sources' },
      { text: '指南', link: '/guide' },
    ],

    // 侧栏按目录结构自动生成：characters/<字类>/<字>
    sidebar: 'auto',

    search: {
      provider: 'local',
      options: {
        detailedView: true,
        miniSearch: {
          searchOptions: {
            fuzzy: 0.2,
            prefix: true,
            boost: { title: 4, char: 3 },
          },
        },
      },
    },

    outline: { level: [2, 3], label: '本页目录' },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/diuci/chinese-oracle-bone-script' },
    ],

    footer: {
      message: '甲骨卜辞原文属公有领域（商代）；我方原创释义、字源解说与选字编排 © 丢词大作战，采用 CC BY 4.0。',
      copyright: '内容来源与授权说明见「数据来源」。',
    },

    lastUpdated: true,
    docFooter: { prev: '上一篇', next: '下一篇' },
  },
})
