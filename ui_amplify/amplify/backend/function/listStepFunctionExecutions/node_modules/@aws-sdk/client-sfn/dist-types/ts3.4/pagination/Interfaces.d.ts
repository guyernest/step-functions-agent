import { PaginationConfiguration } from "@smithy/types";
import { SFNClient } from "../SFNClient";
export interface SFNPaginationConfiguration extends PaginationConfiguration {
  client: SFNClient;
}
