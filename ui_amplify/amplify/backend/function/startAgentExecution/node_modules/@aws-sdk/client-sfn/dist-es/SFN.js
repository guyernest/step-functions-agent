import { createAggregatedClient } from "@smithy/smithy-client";
import { CreateActivityCommand, } from "./commands/CreateActivityCommand";
import { CreateStateMachineAliasCommand, } from "./commands/CreateStateMachineAliasCommand";
import { CreateStateMachineCommand, } from "./commands/CreateStateMachineCommand";
import { DeleteActivityCommand, } from "./commands/DeleteActivityCommand";
import { DeleteStateMachineAliasCommand, } from "./commands/DeleteStateMachineAliasCommand";
import { DeleteStateMachineCommand, } from "./commands/DeleteStateMachineCommand";
import { DeleteStateMachineVersionCommand, } from "./commands/DeleteStateMachineVersionCommand";
import { DescribeActivityCommand, } from "./commands/DescribeActivityCommand";
import { DescribeExecutionCommand, } from "./commands/DescribeExecutionCommand";
import { DescribeMapRunCommand, } from "./commands/DescribeMapRunCommand";
import { DescribeStateMachineAliasCommand, } from "./commands/DescribeStateMachineAliasCommand";
import { DescribeStateMachineCommand, } from "./commands/DescribeStateMachineCommand";
import { DescribeStateMachineForExecutionCommand, } from "./commands/DescribeStateMachineForExecutionCommand";
import { GetActivityTaskCommand, } from "./commands/GetActivityTaskCommand";
import { GetExecutionHistoryCommand, } from "./commands/GetExecutionHistoryCommand";
import { ListActivitiesCommand, } from "./commands/ListActivitiesCommand";
import { ListExecutionsCommand, } from "./commands/ListExecutionsCommand";
import { ListMapRunsCommand } from "./commands/ListMapRunsCommand";
import { ListStateMachineAliasesCommand, } from "./commands/ListStateMachineAliasesCommand";
import { ListStateMachinesCommand, } from "./commands/ListStateMachinesCommand";
import { ListStateMachineVersionsCommand, } from "./commands/ListStateMachineVersionsCommand";
import { ListTagsForResourceCommand, } from "./commands/ListTagsForResourceCommand";
import { PublishStateMachineVersionCommand, } from "./commands/PublishStateMachineVersionCommand";
import { RedriveExecutionCommand, } from "./commands/RedriveExecutionCommand";
import { SendTaskFailureCommand, } from "./commands/SendTaskFailureCommand";
import { SendTaskHeartbeatCommand, } from "./commands/SendTaskHeartbeatCommand";
import { SendTaskSuccessCommand, } from "./commands/SendTaskSuccessCommand";
import { StartExecutionCommand, } from "./commands/StartExecutionCommand";
import { StartSyncExecutionCommand, } from "./commands/StartSyncExecutionCommand";
import { StopExecutionCommand, } from "./commands/StopExecutionCommand";
import { TagResourceCommand } from "./commands/TagResourceCommand";
import { TestStateCommand } from "./commands/TestStateCommand";
import { UntagResourceCommand, } from "./commands/UntagResourceCommand";
import { UpdateMapRunCommand, } from "./commands/UpdateMapRunCommand";
import { UpdateStateMachineAliasCommand, } from "./commands/UpdateStateMachineAliasCommand";
import { UpdateStateMachineCommand, } from "./commands/UpdateStateMachineCommand";
import { ValidateStateMachineDefinitionCommand, } from "./commands/ValidateStateMachineDefinitionCommand";
import { SFNClient } from "./SFNClient";
const commands = {
    CreateActivityCommand,
    CreateStateMachineCommand,
    CreateStateMachineAliasCommand,
    DeleteActivityCommand,
    DeleteStateMachineCommand,
    DeleteStateMachineAliasCommand,
    DeleteStateMachineVersionCommand,
    DescribeActivityCommand,
    DescribeExecutionCommand,
    DescribeMapRunCommand,
    DescribeStateMachineCommand,
    DescribeStateMachineAliasCommand,
    DescribeStateMachineForExecutionCommand,
    GetActivityTaskCommand,
    GetExecutionHistoryCommand,
    ListActivitiesCommand,
    ListExecutionsCommand,
    ListMapRunsCommand,
    ListStateMachineAliasesCommand,
    ListStateMachinesCommand,
    ListStateMachineVersionsCommand,
    ListTagsForResourceCommand,
    PublishStateMachineVersionCommand,
    RedriveExecutionCommand,
    SendTaskFailureCommand,
    SendTaskHeartbeatCommand,
    SendTaskSuccessCommand,
    StartExecutionCommand,
    StartSyncExecutionCommand,
    StopExecutionCommand,
    TagResourceCommand,
    TestStateCommand,
    UntagResourceCommand,
    UpdateMapRunCommand,
    UpdateStateMachineCommand,
    UpdateStateMachineAliasCommand,
    ValidateStateMachineDefinitionCommand,
};
export class SFN extends SFNClient {
}
createAggregatedClient(commands, SFN);
