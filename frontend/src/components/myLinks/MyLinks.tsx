import { useEffect, useMemo, useState } from "react";
import { AgGridReact } from "ag-grid-react";
import {
  AllCommunityModule,
  ModuleRegistry,
  type ColDef,
  type GridApi,
  type GridReadyEvent,
  type ICellRendererParams,
  type IDatasource,
  type IGetRowsParams,
} from "ag-grid-community";
import CopyButton from "../common/copyButton/CopyButton";
import { listUrls, type UrlItem } from "../../services/urls";
import "./MyLinks.css";

ModuleRegistry.registerModules([AllCommunityModule]);

const PAGE_SIZE = 50; // one grid block = one API page

function formatDate(value: string | null | undefined): string {
  return value ? new Date(value).toLocaleString() : "—";
}

function linkStatus(url: UrlItem): string {
  if (url.is_disabled) return "Disabled";
  if (url.expires_at && new Date(url.expires_at) <= new Date())
    return "Expired";
  return "Active";
}

function ShortLinkCell({ data }: ICellRendererParams<UrlItem>) {
  if (!data) return null; // row still loading
  return (
    <span className="mylinks-short">
      <a href={data.short_url} target="_blank" rel="noreferrer">
        {data.short_id}
      </a>
      <CopyButton text={data.short_url} compact />
    </span>
  );
}

const MyLinks: React.FC<{ refreshKey: number }> = ({ refreshKey }) => {
  const [api, setApi] = useState<GridApi<UrlItem> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const columnDefs = useMemo<ColDef<UrlItem>[]>(
    () => [
      {
        headerName: "Short link",
        field: "short_id",
        cellRenderer: ShortLinkCell,
        width: 180,
      },
      {
        headerName: "Destination",
        field: "long_url",
        flex: 1,
        minWidth: 220,
        tooltipField: "long_url",
      },
      {
        headerName: "Clicks",
        field: "click_count",
        width: 100,
        type: "rightAligned",
      },
      {
        headerName: "Created",
        field: "created_at",
        width: 190,
        valueFormatter: (p) => formatDate(p.value),
      },
      {
        headerName: "Expires",
        field: "expires_at",
        width: 190,
        valueFormatter: (p) => formatDate(p.value),
      },
      {
        headerName: "Status",
        colId: "status",
        width: 110,
        valueGetter: (p) => (p.data ? linkStatus(p.data) : ""),
      },
    ],
    [],
  );

  // The grid asks for rows startRow..endRow; that maps directly onto offset/limit.
  const datasource = useMemo<IDatasource>(
    () => ({
      getRows: (params: IGetRowsParams) => {
        listUrls(params.endRow - params.startRow, params.startRow)
          .then((page) => {
            setError(null);
            params.successCallback(page.items, page.total);
          })
          .catch((e: unknown) => {
            setError(
              e instanceof Error ? e.message : "Could not load your links.",
            );
            params.failCallback();
          });
      },
    }),
    [],
  );

  // Reload from the server after a new link is created (refreshKey increments).
  useEffect(() => {
    if (refreshKey > 0) api?.purgeInfiniteCache();
  }, [api, refreshKey]);

  return (
    <section className="mylinks" aria-labelledby="mylinks-title">
      <h2 id="mylinks-title" className="mylinks-title">
        My links
      </h2>
      {error && (
        <p className="mylinks-error" role="alert">
          {error}
        </p>
      )}
      <div className="mylinks-grid">
        <AgGridReact<UrlItem>
          columnDefs={columnDefs}
          defaultColDef={{ sortable: false, resizable: true }}
          rowModelType="infinite"
          datasource={datasource}
          cacheBlockSize={PAGE_SIZE}
          onGridReady={(e: GridReadyEvent<UrlItem>) => setApi(e.api)}
        />
      </div>
    </section>
  );
};

export default MyLinks;
