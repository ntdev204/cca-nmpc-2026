"use client";

import {
  Pagination as ShadcnPagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";

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
  const changePage = (nextPage: number) => (event: React.MouseEvent<HTMLAnchorElement>) => {
    event.preventDefault();
    if (nextPage >= 1 && nextPage <= safeTotalPages && nextPage !== safePage) onPageChange(nextPage);
  };

  return (
    <div className="flex flex-wrap items-center justify-between gap-2 border-t pt-3 text-xs text-muted-foreground">
      <span>{total === undefined ? `Page ${safePage} of ${safeTotalPages}` : `${total} ${label} · page ${safePage} of ${safeTotalPages}`}</span>
      <ShadcnPagination className="mx-0 w-auto justify-end">
        <PaginationContent>
          <PaginationItem>
            <PaginationPrevious
              href="#"
              text=""
              onClick={changePage(safePage - 1)}
              aria-disabled={safePage <= 1}
              className={`size-8 p-0 justify-center ${safePage <= 1 ? "pointer-events-none opacity-50" : ""}`}
            />
          </PaginationItem>
        {pageItems(safePage, safeTotalPages).map((item, index) => item === "ellipsis-left" || item === "ellipsis-right" ? (
          <PaginationItem key={`${item}-${index}`}>
            <PaginationEllipsis />
          </PaginationItem>
        ) : (
          <PaginationItem key={item}>
            <PaginationLink
              href="#"
              size="icon"
              isActive={item === safePage}
              onClick={changePage(item)}
              className={item === safePage ? "bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground" : "border border-border bg-background"}
            >
              {item}
            </PaginationLink>
          </PaginationItem>
        ))}
          <PaginationItem>
            <PaginationNext
              href="#"
              text=""
              onClick={changePage(safePage + 1)}
              aria-disabled={safePage >= safeTotalPages}
              className={`size-8 p-0 justify-center ${safePage >= safeTotalPages ? "pointer-events-none opacity-50" : ""}`}
            />
          </PaginationItem>
        </PaginationContent>
      </ShadcnPagination>
    </div>
  );
}
