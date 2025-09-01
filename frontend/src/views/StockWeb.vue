<template>
  <div class="stock-web-container">
    <div class="table-header">
      <div class="header-left">
        <h2>{{ tableName }}</h2>
        <div class="date-picker-wrapper">
          <i class="fa fa-calendar"></i>
          <input 
            type="text" 
            v-model="currentDate" 
            class="date-picker" 
            :value="oldDate"
          >
        </div>
      </div>
      <div class="header-actions">
        <button @click="resetFilter" class="action-btn">
          <i class="fa fa-refresh"></i>
          重置筛选
        </button>
        <button @click="saveExcel" class="action-btn primary">
          <i class="fa fa-download"></i>
          导出Excel
        </button>
      </div>
    </div>

    <div class="spreadjs-container">
      <div ref="spreadContainer" class="spread-wrapper"></div>
      <div ref="statusBar" class="status-bar"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getStockData } from '@/api/stock'
import dayjs from 'dayjs'

// 导入SpreadJS相关样式
import '@/assets/css/gc.spread.sheets.excel2013white.css'

// 声明 jQuery datepicker 类型
declare global {
  interface JQuery {
    datepicker(options?: any): JQuery
  }
}

// 声明全局函数
declare function saveAs(blob: Blob, filename: string): void

// 声明全局类型
declare global {
  interface Window {
    GC: any
  }
}

const route = useRoute()
const spreadContainer = ref<HTMLElement | null>(null)
const statusBar = ref<HTMLElement | null>(null)
const tableName = ref('')
const currentDate = ref(dayjs().format('YYYY-MM-DD'))
const oldDate = ref('')
const spread = ref<any>(null)
const myView = ref<any>(null)

onMounted(async () => {
  tableName.value = route.query.table_name as string || ''
  await initSpreadJS()
  initDatePicker()
})

const initSpreadJS = async () => {
  if (!spreadContainer.value) return

  try {
    // 动态导入所有必需的脚本
    await Promise.all([
      import(/* @vite-ignore */ '/src/assets/js/gc.spread.sheets.all.min.js'),
      import(/* @vite-ignore */ '/src/assets/js/gc.spread.sheets.resources.zh.min.js'),
      import(/* @vite-ignore */ '/src/assets/js/gc.spread.sheets.tablesheet.min.js'),
      import(/* @vite-ignore */ '/src/assets/js/gc.spread.excelio.min.js'),
      import(/* @vite-ignore */ '/src/assets/js/FileSaver.js')
    ])

    const workbook = new window.GC.Spread.Sheets.Workbook(spreadContainer.value, {
      sheetCount: 0
    })
    
    spread.value = workbook
    workbook.options.newTabVisible = false
    workbook.options.tabEditable = false
    workbook.options.tabNavigationVisible = false
    workbook.options.tabStripRatio = 0.37

    const sheet = workbook.addSheet(0, tableName.value)
    sheet.options.sheetTabColor = 'red'
    sheet.options.allowAddNew = false
    sheet.setDefaultRowHeight(80, window.GC.Spread.Sheets.SheetArea.colHeader)
    sheet.applyTableTheme(window.GC.Spread.Sheets.Tables.TableThemes.light18)

    initStatusBar()
    await loadData()
  } catch (error) {
    console.error('Failed to initialize SpreadJS:', error)
  }
}

const loadData = async () => {
  if (!spread.value) return
  
  try {
    const response = await getStockData(tableName.value, currentDate.value)
    const data = response.data
    
    const dataManager = spread.value.dataManager()
    const productTable = dataManager.addTable("productTable", {
      data: data,
      schema: {
        columns: {
          listing_date: { dataType: "date" },
          report_date: { dataType: "date" },
          plan_date: { dataType: "date" },
          record_date: { dataType: "date" },
          ex_dividend_date: { dataType: "date" }
        }
      }
    })

    const sheet = spread.value.getActiveSheet()
    myView.value = productTable.addView("myView")
    await myView.value.fetch()
    sheet.setDataView(myView.value)
    sheet.togglePinnedColumns([0,1,2])
    updateStatusBar()
  } catch (error) {
    console.error('Failed to load data:', error)
  }
}

const initStatusBar = () => {
  if (!statusBar.value || !spread.value) return

  const StatusItem = window.GC.Spread.Sheets.StatusBar.StatusItem
  class RecordCountItem extends StatusItem {
    cno: number
    dataSourceLength: number
    visibleLength: number
    _element: HTMLElement | null

    constructor(name: string, options: any) {
      super(name, options)
      this.cno = 1
      this.dataSourceLength = 0
      this.visibleLength = 0
      this._element = null
    }

    onCreateItemView(container: HTMLElement) {
      const element = document.createElement("span")
      element.innerHTML = this.getStatusText()
      container.appendChild(element)
      this._element = element
    }

    onUpdate() {
      super.onUpdate()
      if (this._element) {
        this._element.innerHTML = this.getStatusText()
      }
    }

    private getStatusText() {
      return ` <i class="fa fa-info-circle"></i> 总记录/筛选记录：<b>${this.dataSourceLength}</b> / <b>${this.visibleLength}</b> 条 - 当前位置：第 <b>${this.cno}</b> 行`
    }
  }

  const recordCountItem = new RecordCountItem('recordCountItem', {
    menuContent: '当前位置',
    value: 0
  })
  
  const statusBarControl = new window.GC.Spread.Sheets.StatusBar.StatusBar(
    statusBar.value,
    { items: [recordCountItem] }
  )
  
  statusBarControl.bind(spread.value)
}

const updateStatusBar = () => {
  if (!spread.value || !myView.value) return
  
  const statusBarControl = spread.value.statusBar
  if (!statusBarControl) return

  const recordItem = statusBarControl.get("recordCountItem")
  if (recordItem) {
    recordItem.dataSourceLength = myView.value.length()
    recordItem.visibleLength = myView.value.visibleLength()
    recordItem.onUpdate()
  }
}

const initDatePicker = () => {
  $(document).ready(() => {
    $('.date-picker').datepicker({
      language: 'zh-CN',
      format: 'yyyy-mm-dd',
      showOtherMonths: true,
      selectOtherMonths: false,
      autoclose: true,
      todayHighlight: true
    }).on('changeDate', () => {
      loadData()
    })
  })
}

const resetFilter = () => {
  if (!spread.value) return
  const sheet = spread.value.getActiveSheet()
  sheet.rowFilter().reset()
  updateStatusBar()
}

const saveExcel = () => {
  if (!spread.value) return
  const excelIo = new window.GC.Spread.Excel.IO()
  const json = spread.value.toJSON({
    includeBindingSource: true,
    saveAsView: true
  })
  
  excelIo.save(json, (blob: Blob) => {
    saveAs(blob, `${tableName.value}_${currentDate.value}.xlsx`)
  }, (error: Error) => {
    console.error('Export failed:', error)
  })
}

watch(currentDate, (newDate, oldDate) => {
  if (newDate !== oldDate) {
    loadData()
  }
})
</script>

<style scoped>
.stock-web-container {
  height: 100%;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.table-header {
  padding: 20px;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-left h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.5em;
}

.date-picker-wrapper {
  position: relative;
}

.date-picker-wrapper i {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #606266;
}

.date-picker {
  padding: 8px 8px 8px 32px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  width: 140px;
  transition: all 0.3s;
}

.date-picker:focus {
  border-color: #409eff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.header-actions {
  display: flex;
  gap: 12px;
}

.action-btn {
  padding: 8px 16px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: white;
  color: #606266;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s;
}

.action-btn:hover {
  border-color: #409eff;
  color: #409eff;
}

.action-btn.primary {
  background: #409eff;
  border-color: #409eff;
  color: white;
}

.action-btn.primary:hover {
  background: #66b1ff;
  border-color: #66b1ff;
}

.action-btn i {
  font-size: 14px;
}

.spreadjs-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.spread-wrapper {
  flex: 1;
  overflow: hidden;
}

.status-bar {
  height: 24px;
  border-top: 1px solid #ebeef5;
  background: #f8f9fa;
  padding: 0 12px;
  font-size: 12px;
  color: #606266;
  display: flex;
  align-items: center;
}

.status-bar i {
  margin-right: 6px;
  color: #409eff;
}

@media (max-width: 768px) {
  .table-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-left {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .date-picker {
    width: 100%;
  }

  .header-actions {
    flex-direction: column;
  }

  .action-btn {
    width: 100%;
    justify-content: center;
  }
}
</style> 