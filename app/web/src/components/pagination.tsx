"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";

type PaginationProps = {
  page: number;
  totalPages: number;
  total?: number;
  onPageChange: (page: number) => void;
  label?: string;
};

function pageItems(page: number, totalPages: number): Array<number | "ellipsis-left" | "ellipsis-right"> {
  if (totalPages <= 7) return Array.from({ length: totalPages }, (_, index) => index + 1);
  const items: Array<number | "ellipsis-left" | "ellipsis-right"> = [1];
  if (page > 4) items.push("ellipsis-left");
  const start = Math.max(2, page - 1);
  const end = Math.min(totalPages - 1, page + 1);
  for (let value = start; value <= end; value += 1) items.push(value);
  if (page < totalPages - 3) items.push("ellipsis-right");
  items.push(totalPages);
  return items;
}

export function Pagination({ page, totalPages, total, onPageChange, label = "items" }: PaginationProps) {
  const safeTotalPages = Math.max(1, totalPages);
  const safePage = Math.min(Math.max(1, page), safeTotalPages);
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 border-t pt-3 text-xs text-muted-foreground">
      <span>{total === undefined ? `Page ${safePage} of ${safeTotalPages}` : `${total} ${label} · page ${safePage} of ${safeTotalPages}`}</span>
      <div className="flex items-center gap-1" aria-label="Pagination">
        <Button type="button" variant="outline" size="icon-sm" onClick={() => onPageChange(safePage - 1)} disabled={safePage <= 1} aria-label="Previous page">
          <ChevronLeft className="size-4" />
        </Button>
        {pageItems(safePage, safeTotalPages).map((item, index) => item === "ellipsis-left" || item === "ellipsis-right" ? (
          <span key={`${item}-${index}`} className="px-1" aria-hidden="true">…</span>
        ) : (
          <Button key={item} type="button" variant={item === safePage ? "default" : "outline"} size="icon-sm" onClick={() => onPageChange(item)} aria-current={item === safePage ? "page" : undefined}>
            {item}
          </Button>
        ))}
        <Button type="button" variant="outline" size="icon-sm" onClick={() => onPageChange(safePage + 1)} disabled={safePage >= safeTotalPages} aria-label="Next page">
          <ChevronRight className="size-4" />
        </Button>
      </div>
    </div>
  );
}
