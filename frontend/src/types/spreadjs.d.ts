declare module '*.min.js'
declare module '*.js'

declare global {
    interface Window {
        GC: {
            Spread: {
                Sheets: {
                    Workbook: any;
                    SheetArea: any;
                    Tables: {
                        TableThemes: any;
                    };
                    StatusBar: {
                        StatusBar: any;
                        StatusItem: any;
                    };
                };
                Excel: {
                    IO: any;
                };
            };
        };
    }

    function saveAs(blob: Blob, filename: string): void;
}

export { } 