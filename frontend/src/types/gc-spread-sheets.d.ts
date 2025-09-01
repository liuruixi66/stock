declare namespace GC {
    namespace Spread {
        namespace Sheets {
            class Workbook {
                constructor(element: HTMLElement, options?: any)
                options: any
                addSheet(index: number, name: string, sheetType?: any): any
                addSheetTab(index: number, name: string, sheetType?: any): any
                getActiveSheet(): any
                getActiveSheetTab(): any
                dataManager(): any
                suspendPaint(): void
                resumePaint(): void
                refresh(): void
                statusBar: any
            }

            namespace Tables {
                const TableThemes: { [key: string]: any }
            }

            namespace StatusBar {
                class StatusBar {
                    constructor(element: HTMLElement, options: any)
                    bind(spread: any): void
                    get(name: string): any
                }
                class StatusItem {
                    constructor(name: string, options: any)
                    onUpdate(): void
                    onCreateItemView(container: HTMLElement): void
                    _element: HTMLElement
                }
            }

            const SheetArea: { [key: string]: any }
            const SheetType: { [key: string]: any }
            const Events: { [key: string]: string }

            function findControl(element: HTMLElement): any
        }

        namespace Excel {
            class IO {
                save(json: any, callback: (blob: Blob) => void, errorCallback: (error: any) => void): void
            }
        }
    }
} 