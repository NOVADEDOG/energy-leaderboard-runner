/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_APP_TITLE: string
}

interface ImportMeta {
    readonly env: ImportMetaEnv
    readonly glob: <T>(pattern: string, options?: { eager?: boolean; import?: string }) => Record<string, T>
}
