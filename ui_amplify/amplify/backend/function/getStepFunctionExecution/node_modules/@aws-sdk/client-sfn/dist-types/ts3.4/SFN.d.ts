import { HttpHandlerOptions as __HttpHandlerOptions } from "@smithy/types";
import {
  CreateActivityCommandInput,
  CreateActivityCommandOutput,
} from "./commands/CreateActivityCommand";
import {
  CreateStateMachineAliasCommandInput,
  CreateStateMachineAliasCommandOutput,
} from "./commands/CreateStateMachineAliasCommand";
import {
  CreateStateMachineCommandInput,
  CreateStateMachineCommandOutput,
} from "./commands/CreateStateMachineCommand";
import {
  DeleteActivityCommandInput,
  DeleteActivityCommandOutput,
} from "./commands/DeleteActivityCommand";
import {
  DeleteStateMachineAliasCommandInput,
  DeleteStateMachineAliasCommandOutput,
} from "./commands/DeleteStateMachineAliasCommand";
import {
  DeleteStateMachineCommandInput,
  DeleteStateMachineCommandOutput,
} from "./commands/DeleteStateMachineCommand";
import {
  DeleteStateMachineVersionCommandInput,
  DeleteStateMachineVersionCommandOutput,
} from "./commands/DeleteStateMachineVersionCommand";
import {
  DescribeActivityCommandInput,
  DescribeActivityCommandOutput,
} from "./commands/DescribeActivityCommand";
import {
  DescribeExecutionCommandInput,
  DescribeExecutionCommandOutput,
} from "./commands/DescribeExecutionCommand";
import {
  DescribeMapRunCommandInput,
  DescribeMapRunCommandOutput,
} from "./commands/DescribeMapRunCommand";
import {
  DescribeStateMachineAliasCommandInput,
  DescribeStateMachineAliasCommandOutput,
} from "./commands/DescribeStateMachineAliasCommand";
import {
  DescribeStateMachineCommandInput,
  DescribeStateMachineCommandOutput,
} from "./commands/DescribeStateMachineCommand";
import {
  DescribeStateMachineForExecutionCommandInput,
  DescribeStateMachineForExecutionCommandOutput,
} from "./commands/DescribeStateMachineForExecutionCommand";
import {
  GetActivityTaskCommandInput,
  GetActivityTaskCommandOutput,
} from "./commands/GetActivityTaskCommand";
import {
  GetExecutionHistoryCommandInput,
  GetExecutionHistoryCommandOutput,
} from "./commands/GetExecutionHistoryCommand";
import {
  ListActivitiesCommandInput,
  ListActivitiesCommandOutput,
} from "./commands/ListActivitiesCommand";
import {
  ListExecutionsCommandInput,
  ListExecutionsCommandOutput,
} from "./commands/ListExecutionsCommand";
import {
  ListMapRunsCommandInput,
  ListMapRunsCommandOutput,
} from "./commands/ListMapRunsCommand";
import {
  ListStateMachineAliasesCommandInput,
  ListStateMachineAliasesCommandOutput,
} from "./commands/ListStateMachineAliasesCommand";
import {
  ListStateMachinesCommandInput,
  ListStateMachinesCommandOutput,
} from "./commands/ListStateMachinesCommand";
import {
  ListStateMachineVersionsCommandInput,
  ListStateMachineVersionsCommandOutput,
} from "./commands/ListStateMachineVersionsCommand";
import {
  ListTagsForResourceCommandInput,
  ListTagsForResourceCommandOutput,
} from "./commands/ListTagsForResourceCommand";
import {
  PublishStateMachineVersionCommandInput,
  PublishStateMachineVersionCommandOutput,
} from "./commands/PublishStateMachineVersionCommand";
import {
  RedriveExecutionCommandInput,
  RedriveExecutionCommandOutput,
} from "./commands/RedriveExecutionCommand";
import {
  SendTaskFailureCommandInput,
  SendTaskFailureCommandOutput,
} from "./commands/SendTaskFailureCommand";
import {
  SendTaskHeartbeatCommandInput,
  SendTaskHeartbeatCommandOutput,
} from "./commands/SendTaskHeartbeatCommand";
import {
  SendTaskSuccessCommandInput,
  SendTaskSuccessCommandOutput,
} from "./commands/SendTaskSuccessCommand";
import {
  StartExecutionCommandInput,
  StartExecutionCommandOutput,
} from "./commands/StartExecutionCommand";
import {
  StartSyncExecutionCommandInput,
  StartSyncExecutionCommandOutput,
} from "./commands/StartSyncExecutionCommand";
import {
  StopExecutionCommandInput,
  StopExecutionCommandOutput,
} from "./commands/StopExecutionCommand";
import {
  TagResourceCommandInput,
  TagResourceCommandOutput,
} from "./commands/TagResourceCommand";
import {
  TestStateCommandInput,
  TestStateCommandOutput,
} from "./commands/TestStateCommand";
import {
  UntagResourceCommandInput,
  UntagResourceCommandOutput,
} from "./commands/UntagResourceCommand";
import {
  UpdateMapRunCommandInput,
  UpdateMapRunCommandOutput,
} from "./commands/UpdateMapRunCommand";
import {
  UpdateStateMachineAliasCommandInput,
  UpdateStateMachineAliasCommandOutput,
} from "./commands/UpdateStateMachineAliasCommand";
import {
  UpdateStateMachineCommandInput,
  UpdateStateMachineCommandOutput,
} from "./commands/UpdateStateMachineCommand";
import {
  ValidateStateMachineDefinitionCommandInput,
  ValidateStateMachineDefinitionCommandOutput,
} from "./commands/ValidateStateMachineDefinitionCommand";
import { SFNClient } from "./SFNClient";
export interface SFN {
  createActivity(
    args: CreateActivityCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<CreateActivityCommandOutput>;
  createActivity(
    args: CreateActivityCommandInput,
    cb: (err: any, data?: CreateActivityCommandOutput) => void
  ): void;
  createActivity(
    args: CreateActivityCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: CreateActivityCommandOutput) => void
  ): void;
  createStateMachine(
    args: CreateStateMachineCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<CreateStateMachineCommandOutput>;
  createStateMachine(
    args: CreateStateMachineCommandInput,
    cb: (err: any, data?: CreateStateMachineCommandOutput) => void
  ): void;
  createStateMachine(
    args: CreateStateMachineCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: CreateStateMachineCommandOutput) => void
  ): void;
  createStateMachineAlias(
    args: CreateStateMachineAliasCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<CreateStateMachineAliasCommandOutput>;
  createStateMachineAlias(
    args: CreateStateMachineAliasCommandInput,
    cb: (err: any, data?: CreateStateMachineAliasCommandOutput) => void
  ): void;
  createStateMachineAlias(
    args: CreateStateMachineAliasCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: CreateStateMachineAliasCommandOutput) => void
  ): void;
  deleteActivity(
    args: DeleteActivityCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DeleteActivityCommandOutput>;
  deleteActivity(
    args: DeleteActivityCommandInput,
    cb: (err: any, data?: DeleteActivityCommandOutput) => void
  ): void;
  deleteActivity(
    args: DeleteActivityCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DeleteActivityCommandOutput) => void
  ): void;
  deleteStateMachine(
    args: DeleteStateMachineCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DeleteStateMachineCommandOutput>;
  deleteStateMachine(
    args: DeleteStateMachineCommandInput,
    cb: (err: any, data?: DeleteStateMachineCommandOutput) => void
  ): void;
  deleteStateMachine(
    args: DeleteStateMachineCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DeleteStateMachineCommandOutput) => void
  ): void;
  deleteStateMachineAlias(
    args: DeleteStateMachineAliasCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DeleteStateMachineAliasCommandOutput>;
  deleteStateMachineAlias(
    args: DeleteStateMachineAliasCommandInput,
    cb: (err: any, data?: DeleteStateMachineAliasCommandOutput) => void
  ): void;
  deleteStateMachineAlias(
    args: DeleteStateMachineAliasCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DeleteStateMachineAliasCommandOutput) => void
  ): void;
  deleteStateMachineVersion(
    args: DeleteStateMachineVersionCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DeleteStateMachineVersionCommandOutput>;
  deleteStateMachineVersion(
    args: DeleteStateMachineVersionCommandInput,
    cb: (err: any, data?: DeleteStateMachineVersionCommandOutput) => void
  ): void;
  deleteStateMachineVersion(
    args: DeleteStateMachineVersionCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DeleteStateMachineVersionCommandOutput) => void
  ): void;
  describeActivity(
    args: DescribeActivityCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DescribeActivityCommandOutput>;
  describeActivity(
    args: DescribeActivityCommandInput,
    cb: (err: any, data?: DescribeActivityCommandOutput) => void
  ): void;
  describeActivity(
    args: DescribeActivityCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DescribeActivityCommandOutput) => void
  ): void;
  describeExecution(
    args: DescribeExecutionCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DescribeExecutionCommandOutput>;
  describeExecution(
    args: DescribeExecutionCommandInput,
    cb: (err: any, data?: DescribeExecutionCommandOutput) => void
  ): void;
  describeExecution(
    args: DescribeExecutionCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DescribeExecutionCommandOutput) => void
  ): void;
  describeMapRun(
    args: DescribeMapRunCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DescribeMapRunCommandOutput>;
  describeMapRun(
    args: DescribeMapRunCommandInput,
    cb: (err: any, data?: DescribeMapRunCommandOutput) => void
  ): void;
  describeMapRun(
    args: DescribeMapRunCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DescribeMapRunCommandOutput) => void
  ): void;
  describeStateMachine(
    args: DescribeStateMachineCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DescribeStateMachineCommandOutput>;
  describeStateMachine(
    args: DescribeStateMachineCommandInput,
    cb: (err: any, data?: DescribeStateMachineCommandOutput) => void
  ): void;
  describeStateMachine(
    args: DescribeStateMachineCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DescribeStateMachineCommandOutput) => void
  ): void;
  describeStateMachineAlias(
    args: DescribeStateMachineAliasCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DescribeStateMachineAliasCommandOutput>;
  describeStateMachineAlias(
    args: DescribeStateMachineAliasCommandInput,
    cb: (err: any, data?: DescribeStateMachineAliasCommandOutput) => void
  ): void;
  describeStateMachineAlias(
    args: DescribeStateMachineAliasCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DescribeStateMachineAliasCommandOutput) => void
  ): void;
  describeStateMachineForExecution(
    args: DescribeStateMachineForExecutionCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<DescribeStateMachineForExecutionCommandOutput>;
  describeStateMachineForExecution(
    args: DescribeStateMachineForExecutionCommandInput,
    cb: (err: any, data?: DescribeStateMachineForExecutionCommandOutput) => void
  ): void;
  describeStateMachineForExecution(
    args: DescribeStateMachineForExecutionCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: DescribeStateMachineForExecutionCommandOutput) => void
  ): void;
  getActivityTask(
    args: GetActivityTaskCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetActivityTaskCommandOutput>;
  getActivityTask(
    args: GetActivityTaskCommandInput,
    cb: (err: any, data?: GetActivityTaskCommandOutput) => void
  ): void;
  getActivityTask(
    args: GetActivityTaskCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetActivityTaskCommandOutput) => void
  ): void;
  getExecutionHistory(
    args: GetExecutionHistoryCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<GetExecutionHistoryCommandOutput>;
  getExecutionHistory(
    args: GetExecutionHistoryCommandInput,
    cb: (err: any, data?: GetExecutionHistoryCommandOutput) => void
  ): void;
  getExecutionHistory(
    args: GetExecutionHistoryCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: GetExecutionHistoryCommandOutput) => void
  ): void;
  listActivities(): Promise<ListActivitiesCommandOutput>;
  listActivities(
    args: ListActivitiesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListActivitiesCommandOutput>;
  listActivities(
    args: ListActivitiesCommandInput,
    cb: (err: any, data?: ListActivitiesCommandOutput) => void
  ): void;
  listActivities(
    args: ListActivitiesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListActivitiesCommandOutput) => void
  ): void;
  listExecutions(): Promise<ListExecutionsCommandOutput>;
  listExecutions(
    args: ListExecutionsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListExecutionsCommandOutput>;
  listExecutions(
    args: ListExecutionsCommandInput,
    cb: (err: any, data?: ListExecutionsCommandOutput) => void
  ): void;
  listExecutions(
    args: ListExecutionsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListExecutionsCommandOutput) => void
  ): void;
  listMapRuns(
    args: ListMapRunsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListMapRunsCommandOutput>;
  listMapRuns(
    args: ListMapRunsCommandInput,
    cb: (err: any, data?: ListMapRunsCommandOutput) => void
  ): void;
  listMapRuns(
    args: ListMapRunsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListMapRunsCommandOutput) => void
  ): void;
  listStateMachineAliases(
    args: ListStateMachineAliasesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListStateMachineAliasesCommandOutput>;
  listStateMachineAliases(
    args: ListStateMachineAliasesCommandInput,
    cb: (err: any, data?: ListStateMachineAliasesCommandOutput) => void
  ): void;
  listStateMachineAliases(
    args: ListStateMachineAliasesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListStateMachineAliasesCommandOutput) => void
  ): void;
  listStateMachines(): Promise<ListStateMachinesCommandOutput>;
  listStateMachines(
    args: ListStateMachinesCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListStateMachinesCommandOutput>;
  listStateMachines(
    args: ListStateMachinesCommandInput,
    cb: (err: any, data?: ListStateMachinesCommandOutput) => void
  ): void;
  listStateMachines(
    args: ListStateMachinesCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListStateMachinesCommandOutput) => void
  ): void;
  listStateMachineVersions(
    args: ListStateMachineVersionsCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListStateMachineVersionsCommandOutput>;
  listStateMachineVersions(
    args: ListStateMachineVersionsCommandInput,
    cb: (err: any, data?: ListStateMachineVersionsCommandOutput) => void
  ): void;
  listStateMachineVersions(
    args: ListStateMachineVersionsCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListStateMachineVersionsCommandOutput) => void
  ): void;
  listTagsForResource(
    args: ListTagsForResourceCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ListTagsForResourceCommandOutput>;
  listTagsForResource(
    args: ListTagsForResourceCommandInput,
    cb: (err: any, data?: ListTagsForResourceCommandOutput) => void
  ): void;
  listTagsForResource(
    args: ListTagsForResourceCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ListTagsForResourceCommandOutput) => void
  ): void;
  publishStateMachineVersion(
    args: PublishStateMachineVersionCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<PublishStateMachineVersionCommandOutput>;
  publishStateMachineVersion(
    args: PublishStateMachineVersionCommandInput,
    cb: (err: any, data?: PublishStateMachineVersionCommandOutput) => void
  ): void;
  publishStateMachineVersion(
    args: PublishStateMachineVersionCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: PublishStateMachineVersionCommandOutput) => void
  ): void;
  redriveExecution(
    args: RedriveExecutionCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<RedriveExecutionCommandOutput>;
  redriveExecution(
    args: RedriveExecutionCommandInput,
    cb: (err: any, data?: RedriveExecutionCommandOutput) => void
  ): void;
  redriveExecution(
    args: RedriveExecutionCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: RedriveExecutionCommandOutput) => void
  ): void;
  sendTaskFailure(
    args: SendTaskFailureCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<SendTaskFailureCommandOutput>;
  sendTaskFailure(
    args: SendTaskFailureCommandInput,
    cb: (err: any, data?: SendTaskFailureCommandOutput) => void
  ): void;
  sendTaskFailure(
    args: SendTaskFailureCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: SendTaskFailureCommandOutput) => void
  ): void;
  sendTaskHeartbeat(
    args: SendTaskHeartbeatCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<SendTaskHeartbeatCommandOutput>;
  sendTaskHeartbeat(
    args: SendTaskHeartbeatCommandInput,
    cb: (err: any, data?: SendTaskHeartbeatCommandOutput) => void
  ): void;
  sendTaskHeartbeat(
    args: SendTaskHeartbeatCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: SendTaskHeartbeatCommandOutput) => void
  ): void;
  sendTaskSuccess(
    args: SendTaskSuccessCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<SendTaskSuccessCommandOutput>;
  sendTaskSuccess(
    args: SendTaskSuccessCommandInput,
    cb: (err: any, data?: SendTaskSuccessCommandOutput) => void
  ): void;
  sendTaskSuccess(
    args: SendTaskSuccessCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: SendTaskSuccessCommandOutput) => void
  ): void;
  startExecution(
    args: StartExecutionCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<StartExecutionCommandOutput>;
  startExecution(
    args: StartExecutionCommandInput,
    cb: (err: any, data?: StartExecutionCommandOutput) => void
  ): void;
  startExecution(
    args: StartExecutionCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: StartExecutionCommandOutput) => void
  ): void;
  startSyncExecution(
    args: StartSyncExecutionCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<StartSyncExecutionCommandOutput>;
  startSyncExecution(
    args: StartSyncExecutionCommandInput,
    cb: (err: any, data?: StartSyncExecutionCommandOutput) => void
  ): void;
  startSyncExecution(
    args: StartSyncExecutionCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: StartSyncExecutionCommandOutput) => void
  ): void;
  stopExecution(
    args: StopExecutionCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<StopExecutionCommandOutput>;
  stopExecution(
    args: StopExecutionCommandInput,
    cb: (err: any, data?: StopExecutionCommandOutput) => void
  ): void;
  stopExecution(
    args: StopExecutionCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: StopExecutionCommandOutput) => void
  ): void;
  tagResource(
    args: TagResourceCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<TagResourceCommandOutput>;
  tagResource(
    args: TagResourceCommandInput,
    cb: (err: any, data?: TagResourceCommandOutput) => void
  ): void;
  tagResource(
    args: TagResourceCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: TagResourceCommandOutput) => void
  ): void;
  testState(
    args: TestStateCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<TestStateCommandOutput>;
  testState(
    args: TestStateCommandInput,
    cb: (err: any, data?: TestStateCommandOutput) => void
  ): void;
  testState(
    args: TestStateCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: TestStateCommandOutput) => void
  ): void;
  untagResource(
    args: UntagResourceCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UntagResourceCommandOutput>;
  untagResource(
    args: UntagResourceCommandInput,
    cb: (err: any, data?: UntagResourceCommandOutput) => void
  ): void;
  untagResource(
    args: UntagResourceCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: UntagResourceCommandOutput) => void
  ): void;
  updateMapRun(
    args: UpdateMapRunCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UpdateMapRunCommandOutput>;
  updateMapRun(
    args: UpdateMapRunCommandInput,
    cb: (err: any, data?: UpdateMapRunCommandOutput) => void
  ): void;
  updateMapRun(
    args: UpdateMapRunCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: UpdateMapRunCommandOutput) => void
  ): void;
  updateStateMachine(
    args: UpdateStateMachineCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UpdateStateMachineCommandOutput>;
  updateStateMachine(
    args: UpdateStateMachineCommandInput,
    cb: (err: any, data?: UpdateStateMachineCommandOutput) => void
  ): void;
  updateStateMachine(
    args: UpdateStateMachineCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: UpdateStateMachineCommandOutput) => void
  ): void;
  updateStateMachineAlias(
    args: UpdateStateMachineAliasCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<UpdateStateMachineAliasCommandOutput>;
  updateStateMachineAlias(
    args: UpdateStateMachineAliasCommandInput,
    cb: (err: any, data?: UpdateStateMachineAliasCommandOutput) => void
  ): void;
  updateStateMachineAlias(
    args: UpdateStateMachineAliasCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: UpdateStateMachineAliasCommandOutput) => void
  ): void;
  validateStateMachineDefinition(
    args: ValidateStateMachineDefinitionCommandInput,
    options?: __HttpHandlerOptions
  ): Promise<ValidateStateMachineDefinitionCommandOutput>;
  validateStateMachineDefinition(
    args: ValidateStateMachineDefinitionCommandInput,
    cb: (err: any, data?: ValidateStateMachineDefinitionCommandOutput) => void
  ): void;
  validateStateMachineDefinition(
    args: ValidateStateMachineDefinitionCommandInput,
    options: __HttpHandlerOptions,
    cb: (err: any, data?: ValidateStateMachineDefinitionCommandOutput) => void
  ): void;
}
export declare class SFN extends SFNClient implements SFN {}
