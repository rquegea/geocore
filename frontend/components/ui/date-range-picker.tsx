"use client"

import { useState, useCallback } from "react"
import { format } from "date-fns"
import { es } from "date-fns/locale"
import { DateRange } from "react-day-picker"
import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Calendar } from "@/components/ui/calendar"
import { Calendar as CalendarIcon } from "lucide-react"
import { cn } from "@/lib/utils"

type DateRangePickerProps = {
  value?: DateRange | undefined
  onChange?: (next: DateRange | undefined) => void
  className?: string
  buttonClassName?: string
  placeholder?: string
}

export function DateRangePicker({ value, onChange, className, buttonClassName, placeholder = "Elige una fecha" }: DateRangePickerProps) {
  const [open, setOpen] = useState(false)

  const handleSelect = useCallback(
    (range: DateRange | undefined) => {
      onChange?.(range)
      if (range?.from && range?.to) {
        setOpen(false)
      }
    },
    [onChange]
  )

  return (
    <div className={cn(className)}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            id="date"
            variant="outline"
            className={cn(
              "w-[260px] justify-start text-left font-normal shadow-sm bg-white border-gray-200",
              buttonClassName,
              !value && "text-muted-foreground"
            )}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {value?.from ? (
              value.to ? (
                <>
                  {format(value.from, "dd LLL y", { locale: es })} - {format(value.to, "dd LLL y", { locale: es })}
                </>
              ) : (
                format(value.from, "dd LLL y", { locale: es })
              )
            ) : (
              <span>{placeholder}</span>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[280px] p-2" align="start" side="bottom" sideOffset={6}>
          <Calendar initialFocus mode="range" defaultMonth={value?.from} selected={value} onSelect={handleSelect} numberOfMonths={1} />
        </PopoverContent>
      </Popover>
    </div>
  )
}


