/**
 * 日期处理工具函数
 */

/**
 * 格式化日期为YYYY-MM-DD格式
 * @param date 日期对象或字符串
 * @returns 格式化后的日期字符串
 */
export function formatDate(date: Date | string): string {
  if (!date) return ''
  
  const d = new Date(date)
  if (isNaN(d.getTime())) return ''
  
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  
  return `${year}-${month}-${day}`
}

/**
 * 将日期字符串转换为YYYYMMDD格式
 * @param dateString YYYY-MM-DD格式的日期字符串
 * @returns YYYYMMDD格式的日期字符串
 */
export function dateToApiFormat(dateString: string): string {
  if (!dateString) return ''
  return dateString.replace(/-/g, '')
}

/**
 * 将YYYYMMDD格式转换为YYYY-MM-DD格式
 * @param apiDate YYYYMMDD格式的日期字符串
 * @returns YYYY-MM-DD格式的日期字符串
 */
export function apiDateToDisplayFormat(apiDate: string): string {
  if (!apiDate || apiDate.length !== 8) return ''
  
  const year = apiDate.substring(0, 4)
  const month = apiDate.substring(4, 6)
  const day = apiDate.substring(6, 8)
  
  return `${year}-${month}-${day}`
}

/**
 * 获取当前日期的YYYY-MM-DD格式
 * @returns 当前日期字符串
 */
export function getCurrentDate(): string {
  return formatDate(new Date())
}

/**
 * 获取指定天数前的日期
 * @param days 天数
 * @returns 日期字符串
 */
export function getDaysAgo(days: number): string {
  const date = new Date()
  date.setDate(date.getDate() - days)
  return formatDate(date)
}

/**
 * 验证日期格式是否正确
 * @param dateString 日期字符串
 * @returns 是否为有效日期
 */
export function isValidDate(dateString: string): boolean {
  if (!dateString) return false
  
  const date = new Date(dateString)
  return !isNaN(date.getTime())
}

/**
 * 比较两个日期的大小
 * @param date1 第一个日期
 * @param date2 第二个日期
 * @returns 1: date1 > date2, 0: 相等, -1: date1 < date2
 */
export function compareDates(date1: string, date2: string): number {
  const d1 = new Date(date1)
  const d2 = new Date(date2)
  
  if (d1.getTime() > d2.getTime()) return 1
  if (d1.getTime() < d2.getTime()) return -1
  return 0
}

/**
 * 获取日期范围内的天数
 * @param startDate 开始日期
 * @param endDate 结束日期
 * @returns 天数
 */
export function getDaysBetween(startDate: string, endDate: string): number {
  const start = new Date(startDate)
  const end = new Date(endDate)
  
  const diffTime = Math.abs(end.getTime() - start.getTime())
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  
  return diffDays
}

/**
 * 默认的时间范围设置
 */
export const DEFAULT_DATE_RANGES = {
  // 最近一年
  LAST_YEAR: {
    start: getDaysAgo(365),
    end: getCurrentDate()
  },
  // 最近半年
  LAST_HALF_YEAR: {
    start: getDaysAgo(180),
    end: getCurrentDate()
  },
  // 最近一个季度
  LAST_QUARTER: {
    start: getDaysAgo(90),
    end: getCurrentDate()
  },
  // 最近一个月
  LAST_MONTH: {
    start: getDaysAgo(30),
    end: getCurrentDate()
  },
  // 今年至今
  YEAR_TO_DATE: {
    start: new Date().getFullYear() + '-01-01',
    end: getCurrentDate()
  }
}
