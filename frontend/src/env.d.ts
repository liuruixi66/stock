/// <reference types="vite/client" />

declare module '*.vue' {
    import type { DefineComponent } from 'vue'
    const component: DefineComponent<{}, {}, any>
    export default component
}

declare module '@grapecity/spread-sheets-vue'
declare module '@grapecity/spread-sheets'
declare module '@grapecity/spread-excelio' 