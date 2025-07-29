import { createPaginator } from "@smithy/core";
import { GetExecutionHistoryCommand, } from "../commands/GetExecutionHistoryCommand";
import { SFNClient } from "../SFNClient";
export const paginateGetExecutionHistory = createPaginator(SFNClient, GetExecutionHistoryCommand, "nextToken", "nextToken", "maxResults");
