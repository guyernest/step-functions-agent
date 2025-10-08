/* tslint:disable */
/* eslint-disable */
export function init_panic_hook(): void;
export class PmcpWasmClient {
  free(): void;
  constructor(server_url: string);
  /**
   * Initialize the MCP connection using pmcp WasmHttpClient
   */
  initialize(): Promise<any>;
  /**
   * List all available tools using pmcp
   */
  list_tools(): Promise<any>;
  /**
   * Call a tool using pmcp
   */
  call_tool(tool_name: string, _arguments: any): Promise<any>;
}

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
  readonly memory: WebAssembly.Memory;
  readonly init_panic_hook: () => void;
  readonly __wbg_pmcpwasmclient_free: (a: number, b: number) => void;
  readonly pmcpwasmclient_new: (a: number, b: number) => number;
  readonly pmcpwasmclient_initialize: (a: number) => any;
  readonly pmcpwasmclient_list_tools: (a: number) => any;
  readonly pmcpwasmclient_call_tool: (a: number, b: number, c: number, d: any) => any;
  readonly __wbindgen_malloc: (a: number, b: number) => number;
  readonly __wbindgen_realloc: (a: number, b: number, c: number, d: number) => number;
  readonly __wbindgen_exn_store: (a: number) => void;
  readonly __externref_table_alloc: () => number;
  readonly __wbindgen_export_4: WebAssembly.Table;
  readonly __wbindgen_free: (a: number, b: number, c: number) => void;
  readonly __wbindgen_export_6: WebAssembly.Table;
  readonly closure174_externref_shim: (a: number, b: number, c: any) => void;
  readonly closure196_externref_shim: (a: number, b: number, c: any, d: any) => void;
  readonly __wbindgen_start: () => void;
}

export type SyncInitInput = BufferSource | WebAssembly.Module;
/**
* Instantiates the given `module`, which can either be bytes or
* a precompiled `WebAssembly.Module`.
*
* @param {{ module: SyncInitInput }} module - Passing `SyncInitInput` directly is deprecated.
*
* @returns {InitOutput}
*/
export function initSync(module: { module: SyncInitInput } | SyncInitInput): InitOutput;

/**
* If `module_or_path` is {RequestInfo} or {URL}, makes a request and
* for everything else, calls `WebAssembly.instantiate` directly.
*
* @param {{ module_or_path: InitInput | Promise<InitInput> }} module_or_path - Passing `InitInput` directly is deprecated.
*
* @returns {Promise<InitOutput>}
*/
export default function __wbg_init (module_or_path?: { module_or_path: InitInput | Promise<InitInput> } | InitInput | Promise<InitInput>): Promise<InitOutput>;
