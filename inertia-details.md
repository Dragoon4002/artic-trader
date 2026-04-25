> ## Documentation Index
> Fetch the complete documentation index at: https://docs.initia.xyz/llms.txt
> Use this file to discover all available pages before exploring further.

# Set Up Your Appchain

## Build an Appchain with Your AI Agent

Welcome to the hackathon! This guide will walk you through building an appchain
from scratch. You'll go from a simple idea to a functioning appchain and
frontend efficiently.

## Step 1: Prepare Your Workspace

Before installing tools or initializing your appchain, create a dedicated
directory for your project. This keeps your configuration files, VM binaries,
and smart contracts organized in one place.

**Run the following commands in your terminal:**

```bash wrap theme={null}
mkdir my-initia-project
cd my-initia-project
```

## Step 2: Install Your AI Skill

Your AI agent needs the `Initia Appchain Dev` skill to help you manage
your appchain, write smart contracts, and build your frontend.

**Run the following command in your terminal:**

```bash wrap theme={null}
npx skills add initia-labs/agent-skills
```

## Step 3: Select an AI Agent

These guides assume you are using a code-aware AI agent that can access your
project directory, read files, run commands, and help you edit code. Any
equivalent tool is fine.

### Terminal Agents (CLI)

* [OpenAI Codex](https://help.openai.com/en/articles/11096431-openai-codex-ci-getting-started)
* [Claude Code](https://code.claude.com/docs/en/setup)
* [Gemini CLI](https://geminicli.com/docs/get-started/installation/)

### AI-Powered IDEs

* [Cursor](https://cursor.com/download)
* [VS Code](https://code.visualstudio.com/download)

Keep your AI agent open in your project root so it can use your local context
when you paste the prompts in this guide.

<Tip>
  **Recommended setup:** Use two terminal tabs or a split-screen layout:

  1. **AI agent**: For high-level tasks, contract generation, and
     troubleshooting.
  2. **Standard terminal**: For interactive CLI commands like `weave init` and
     long-running builds.
</Tip>

## Step 4: Select Your Track & VM

Before installing tools, decide what you want to build. This choice determines
which `Virtual Machine (VM)` your AI agent will set up for you.

| Track                  | Recommended VM   | Reason                                                       |
| :--------------------- | :--------------- | :----------------------------------------------------------- |
| `Gaming / Consumer`    | `Move`           | Best for complex onchain logic and object-oriented assets.   |
| `DeFi / Institutional` | `EVM` (Solidity) | Best for leveraging existing Ethereum tooling and libraries. |
| `AI / Tooling`         | `Wasm` (Rust)    | Best for backend-heavy apps, agents, and tooling.            |

<Note>
  If you are building for the AI track and want guidance on where AI should
  live in your architecture, see
  [AI Track Guidance](/hackathon/ai-track-guidance).
</Note>

## Step 5: Prerequisites Checklist

To ensure a smooth setup, verify you have the following system tools installed:

* **[Docker Desktop](https://www.docker.com/products/docker-desktop/)**: Required for running the bridge bots and relayer. **Must be running.**
* **[Go (1.22+)](https://go.dev/doc/install)**: Required to build the appchain binaries.
* **Track Specifics**:
  * **Move**: No extra tools required.
  * **EVM**: **[Foundry](https://book.getfoundry.sh/getting-started/installation)** (Forge) is recommended for contract development.
  * **Wasm**: **[Rust & Cargo](https://rustup.rs/)** are required for contract development.

## Step 6: AI-Powered Initia Tool Setup and Verification

Now, ask your AI agent to handle the Initia-specific tools. It will install the core CLIs (`weave`, `initiad`, `jq`), build your chosen VM binary (`minitiad`), and verify everything is in your `PATH`.

Replace `<MOVE / EVM / WASM>` with your selected track from Step 4 (`Move`, `EVM`, or `Wasm`).

```terminal title="Prompt: Set up my environment" wrap theme={null}
Using the `initia-appchain-dev` skill, please set up my environment for the <MOVE / EVM / WASM> track.
```

### Verify Installation & PATH

After setup completes, your AI agent can verify the tools are accessible from
anywhere on your system.

```terminal title="Prompt: Verify tool installation" wrap theme={null}
Using the `initia-appchain-dev` skill, please verify that `initiad`, `weave`, and `minitiad` are properly installed and accessible in my PATH.
```

## Step 7: Initial Setup with `weave init`

Your AI agent is your partner in this hackathon, but the `weave` CLI requires
an interactive setup flow to prepare your environment and launch your appchain.
You can run it whenever you need to initialize or reconfigure your setup.

<Warning>
  **Resetting Existing Local State:** If you already ran `weave init` and want to create a new appchain, run the
  following commands first. This clears your existing local Initia, Minitia,
  OPinit, and relayer setup:

  ```bash wrap theme={null}
  rm -rf ~/.weave ~/.initia ~/.minitia ~/.opinit
  docker rm -f weave-relayer || true
  ```
</Warning>

**Run the following command in your terminal:**

```bash wrap theme={null}
weave init
```

Here's a guide on how to navigate the interactive setup:

<Steps>
  <Step title="Foundation & Funding">
    ### Generate Gas Station Account

    The Gas Station is an account on the Initia L1 that will fund your rollup's infrastructure.

    **Prompt:**

    ```terminal wrap theme={null}
    How would you like to set up your Gas Station account?
    ```

    **Action:**
    Select `Generate new account (recommended)`.

    **Result:**
    You will see your new Gas Station Address. Copy this address.

    ### Fund Your Gas Station Account

    **Action:**
    Go to the [Initia Testnet Faucet](https://app.testnet.initia.xyz/faucet).

    **Action:**
    Paste your address and click **Submit** to receive testnet INIT tokens.

    **Prompt:**

    ```terminal wrap theme={null}
    Type `continue` to proceed.
    ```

    **Action:**
    Type `continue` and press Enter.
  </Step>

  <Step title="Rollup Identity">
    ### Select Your Action

    **Prompt:**

    ```terminal wrap theme={null}
    What do you want to do?
    ```

    **Action:**
    Select `Launch a new rollup`.

    <Warning>
      **Switching VMs?** Reinstall the correct `minitiad` binary first (Step 6). If you have existing rollup data, type `confirm` when prompted to clean it and proceed.
    </Warning>

    ### Select L1 Network

    **Prompt:**

    ```terminal wrap theme={null}
    Select the Initia L1 network
    ```

    **Action:**
    Select `Testnet (initiation-2)`.

    ### Select Virtual Machine (VM)

    **Prompt:**

    ```terminal wrap theme={null}
    Select the Virtual Machine (VM)
    ```

    **Action:**
    Select your desired VM (e.g., `Move`).

    ### Specify Rollup Chain ID

    **Prompt:**

    ```terminal wrap theme={null}
    Specify rollup chain ID
    ```

    **Action:**
    Enter a unique ID (e.g., `mygame-1`).

    <Tip>
      **Save your Chain ID!** You'll need this unique identifier for your final submission.
    </Tip>

    ### Specify Rollup Gas Denom

    **Prompt:**

    ```terminal wrap theme={null}
    Specify rollup gas denom
    ```

    **Action:**
    Press `Tab` for default (`umin`) or enter your own.

    ### Specify Rollup Node Moniker

    **Prompt:**

    ```terminal wrap theme={null}
    Specify rollup node moniker
    ```

    **Action:**
    Press `Tab` for default (`operator`).
  </Step>

  <Step title="Network & Infrastructure">
    ### Submission Interval

    **Prompt:**

    ```terminal wrap theme={null}
    Specify OP bridge config: Submission Interval
    ```

    **Action:**
    Press `Tab` for default (`1m`).

    ### Finalization Period

    **Prompt:**

    ```terminal wrap theme={null}
    Specify OP bridge config: Output Finalization Period
    ```

    **Action:**
    Press `Tab` for default (`168h`).

    ### Data Availability

    **Prompt:**

    ```terminal wrap theme={null}
    Where should the rollup blocks data be submitted?
    ```

    **Action:**
    Select `Initia L1`.

    ### Enable Oracle Price Feed

    **Prompt:**

    ```terminal wrap theme={null}
    Would you like to enable oracle price feed from L1?
    ```

    **Action:**
    Select `Enable`.
  </Step>

  <Step title="Security & Genesis">
    ### Setup Method for System Keys

    **Prompt:**

    ```terminal wrap theme={null}
    Select a setup method for the system keys
    ```

    **Action:**
    Select `Generate new system keys`.

    ### System Accounts Funding Option

    **Prompt:**

    ```terminal wrap theme={null}
    Select system accounts funding option
    ```

    **Action:**
    Select `Use the default preset`.

    ### Specify Fee Whitelist Addresses

    **Prompt:**

    ```terminal wrap theme={null}
    Specify fee whitelist addresses
    ```

    **Action:**
    Press `Enter` to leave empty.

    ### Add Gas Station Account to Genesis

    **Prompt:**

    ```terminal wrap theme={null}
    Would you like to add the Gas Station account to genesis accounts?
    ```

    **Action:**
    Select `Yes`.

    ### Specify Genesis Balance

    **Prompt:**

    ```terminal wrap theme={null}
    Specify the genesis balance for the Gas Station account
    ```

    **Action:**
    Enter `1000000000000000000000000` (10^24). This ensures you have plenty of tokens for testing, especially for EVM.

    <Warning>
      **Move Track Balance Limit:** Use `10000000000000000000` (10^19) to avoid `u64` overflows.
    </Warning>

    ### Add Additional Genesis Accounts

    **Prompt:**

    ```terminal wrap theme={null}
    Would you like to add genesis accounts?
    ```

    **Action:**
    Select `No`.
  </Step>

  <Step title="Launch">
    ### Verify System Keys & Continue

    **Prompt:**

    ```terminal wrap theme={null}
    Type 'continue' to proceed.
    ```

    **Action:**
    Type `continue` and press Enter.

    ### Confirm Transactions

    **Prompt:**

    ```terminal wrap theme={null}
    Confirm to proceed with signing and broadcasting the following transactions? [y]:
    ```

    **Action:**
    Type `y` and press Enter.

    Your appchain will now launch and start producing blocks!
  </Step>
</Steps>

## Step 8: Setup Interwoven Bots

To enable the Optimistic bridge and cross-chain communication (IBC) between
Initia L1 and your appchain, you need to start the `OPinit Executor` and the
`IBC Relayer`. These bots manage the cross-chain connectivity of your chain.

<Note>
  **Prerequisite:** Your appchain must be running before configuring these bots. Because `weave init` runs your chain in the background, you can continue using the same terminal window.
</Note>

### 8.1 Start the OPinit Executor

The executor handles the submission of rollup data and bridge operations.

**Run the following command:**

```bash wrap theme={null}
weave opinit init executor
```

Follow the interactive guide:

<Steps>
  <Step title="Use Detected Keys">
    **Prompt:**

    ```terminal wrap theme={null}
    Existing keys in config.json detected. Would you like to add these to the keyring before proceeding?
    ```

    **Action:**
    Select `Yes, use detected keys`.
  </Step>

  <Step title="System Key for Oracle">
    **Prompt:**

    ```terminal wrap theme={null}
    Please select an option for the system key for Oracle Bridge Executor
    ```

    **Action:**
    Select `Generate new system key`.
  </Step>

  <Step title="Pre-fill Data">
    **Prompt:**

    ```terminal wrap theme={null}
    Existing config.json detected. Would you like to use the data in this file to pre-fill some fields?
    ```

    **Action:**
    Select `Yes, prefill`.
  </Step>

  <Step title="Listen Address">
    **Prompt:**

    ```terminal wrap theme={null}
    Specify listen address of the bot
    ```

    **Action:**
    Press `Tab` to use `localhost:3000` (ensure nothing else is running on this port).
  </Step>

  <Step title="Finalize Configuration">
    **Action:**
    Press `Enter` for L1 RPC, Chain ID, and Gas Denom. For Rollup RPC, press `Tab` to use `http://localhost:26657`.
  </Step>

  <Step title="Start the Bot">
    Once initialized, start the bot in the background:

    ```bash wrap theme={null}
    weave opinit start executor -d
    ```
  </Step>
</Steps>

### 8.2 Start the IBC Relayer

The relayer enables asset transfers (like INIT) between the L1 and your
appchain.

<Warning>Docker Desktop must be running to launch the relayer.</Warning>

**Run the following command:**

```bash wrap theme={null}
weave relayer init
```

Follow the interactive guide:

<Steps>
  <Step title="Select Rollup">
    **Prompt:**

    ```terminal wrap theme={null}
    Select the type of Interwoven rollup you want to relay
    ```

    **Action:**
    Select `Local Rollup (<YOUR_APPCHAIN_ID>)`.
  </Step>

  <Step title="Endpoints">
    **Action:**
    Press `Tab` for both **RPC** (`http://localhost:26657`) and **REST** (`http://localhost:1317`) endpoints.
  </Step>

  <Step title="Channel Method">
    **Prompt:**

    ```terminal wrap theme={null}
    Select method to set up IBC channels for the relayer
    ```

    **Action:**
    Select `Subscribe to only transfer and nft-transfer IBC Channels (minimal setup)`.
  </Step>

  <Step title="Select Channels">
    **Prompt:**

    ```terminal wrap theme={null}
    Select the IBC channels you would like to relay
    ```

    **Action:**
    Press `Space` to select all (transfer and nft-transfer), then press `Enter`.
  </Step>

  <Step title="Challenger Key">
    **Prompt:**

    ```terminal wrap theme={null}
    Do you want to set up relayer with the challenger key
    ```

    **Action:**
    Select `Yes (recommended)`.
  </Step>

  <Step title="Start Relayer">
    Start the relayer process:

    ```bash wrap theme={null}
    weave relayer start -d
    ```

    <Note>
      You can view relayer logs at any time by running `weave relayer log` in your terminal.
    </Note>
  </Step>
</Steps>

<Note>
  **Persistence After Restart:**
  After restarting your computer, the relayer remains managed by Docker. As
  long as Docker Desktop is open, it should still be running. You still need to
  restart your rollup full node and executor:

  ```bash wrap theme={null}
  weave rollup start -d

  weave opinit start executor -d
  ```
</Note>

## Step 9: Final Key Setup

**Why:** The `Gas Station` account acts as your `Universal Developer
Key`. Importing it allows you to sign transactions manually via the CLI, and it
enables your AI co-pilot to deploy contracts and interact with your appchain.

**Action:** Run these commands to import your account into both the L1
(`initiad`) and L2 (`minitiad`) keychains:

```bash wrap theme={null}
# Extract your mnemonic from the weave config
MNEMONIC=$(jq -r '.common.gas_station.mnemonic' ~/.weave/config.json)

# Import into initiad (L1)
initiad keys add gas-station --recover --keyring-backend test --coin-type 60 --key-type eth_secp256k1 --source <(echo -n "$MNEMONIC")

# Import into minitiad (L2)
minitiad keys add gas-station --recover --keyring-backend test --coin-type 60 --key-type eth_secp256k1 --source <(echo -n "$MNEMONIC")
```

**Action:** Verify the import by listing your keys to ensure `gas-station`
appears in both:

```bash wrap theme={null}
# Verify L1 keys
initiad keys list --keyring-backend test

# Verify L2 keys
minitiad keys list --keyring-backend test
```

<Warning>
  **Production Security:** This workflow is for rapid prototyping only.

  * **Insecure Storage:** `config.json` and `--keyring-backend test` are for convenience, not production.
  * **Mainnet:** Use secure keyrings (OS keychain, hardware wallet) and never store mnemonics in plaintext.
  * **Best Practice:** Use separate accounts for `Gas Station`, `Validator`, and `Developer` roles on Mainnet.
</Warning>

## Step 10: Verifying Your Appchain

After completing the infrastructure setup, verify that everything is healthy.

```terminal title="Prompt: Verify my appchain is healthy" wrap theme={null}
Using the `initia-appchain-dev` skill, please verify that my appchain, executor bot, and relayer are running and that my Gas Station account has a balance.
```

## Step 11: Build Your App

Congratulations! You have successfully launched your first appchain. Next, head
to the [Builder Guide](/hackathon/builder-guide) to select whether to build
from scratch or start from a Blueprint, then build your app with AI, debug
issues, and prepare your submission.


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.initia.xyz/llms.txt
> Use this file to discover all available pages before exploring further.

# Submission Requirements

Use this page to prepare your final submission. Complete the required
submission files and fill in any missing details before you submit.

## Requirements

If you followed [Set Up Your Appchain](/hackathon/get-started) and completed
one of the Blueprint tutorials, you likely already satisfy the first three
requirements below: appchain deployment, frontend experience, and native
feature. Use this section to verify those pieces and complete the required
submission files.

<CardGroup cols={2}>
  <Card title="Appchain Deployment" icon="diagram-project">
    Your project should run as its own Initia appchain, with its own rollup
    identity and deployed application logic.
  </Card>

  <Card title="Frontend Experience" icon="display">
    Your frontend should use `InterwovenKit` for wallet connection and
    transaction flows so the app reflects the core Initia user experience.
  </Card>

  <Card title="Native Feature" icon="bolt">
    Your project should implement at least one supported Native Feature:

    * `auto-signing`
    * `interwoven-bridge`
    * `initia-usernames`
  </Card>

  <Card title="Submission Files" icon="file-lines">
    Your repository should include:

    * `.initia/submission.json`
    * `README.md` at the repository root
  </Card>
</CardGroup>

<Note>
  **Showcase your app's originality:** Projects that only reproduce a Blueprint without
  meaningful customization are not eligible for prizes. Your submission should
  include clear custom logic, UX, or product differentiation.
</Note>

## Submission JSON

Required file path: `.initia/submission.json`

Use this exact structure:

```json title=".initia/submission.json" theme={null}
{
  "project_name": "My Project",
  "repo_url": "https://github.com/<org>/<repo>",
  "commit_sha": "0123456789abcdef0123456789abcdef01234567",
  "rollup_chain_id": "my-game-1",
  "deployed_address": "0x...",
  "vm": "move",
  "native_feature": "auto-signing",
  "core_logic_path": "blockforge/sources/items.move",
  "native_feature_frontend_path": "blockforge-frontend/src/Game.jsx",
  "demo_video_url": "https://youtu.be/..."
}
```

## Submission JSON Field Reference

All fields in `.initia/submission.json` are required.

| Field                          | Expected value                                                                                                           |
| :----------------------------- | :----------------------------------------------------------------------------------------------------------------------- |
| `project_name`                 | Non-empty string                                                                                                         |
| `repo_url`                     | Reachable public GitHub repository URL                                                                                   |
| `commit_sha`                   | 40-character hex Git commit SHA                                                                                          |
| `rollup_chain_id`              | Non-empty string                                                                                                         |
| `deployed_address`             | Primary deployed address for your application logic. Use your contract address, or your module address for Move projects |
| `vm`                           | `move`, `evm`, or `wasm`                                                                                                 |
| `native_feature`               | `auto-signing`, `interwoven-bridge`, or `initia-usernames`                                                               |
| `core_logic_path`              | Repo-relative file path that must exist at `commit_sha`                                                                  |
| `native_feature_frontend_path` | Repo-relative file path that must exist at `commit_sha`                                                                  |
| `demo_video_url`               | Public Loom or YouTube URL for a 1 to 3 minute walkthrough video                                                         |

## Project Description

Required file path: `README.md` at the repository root

Copy this block near the top of your `README.md` and fill it in:

```markdown title="README.md" theme={null}
## Initia Hackathon Submission

- **Project Name**: [Your Project Name]

### Project Overview

[Provide a 2-3 sentence description of your application, the problem it solves,
who it is for, and why it is valuable to users.]

### Implementation Detail

- **The Custom Implementation**: Briefly describe the unique logic you added.
  What original functionality did you design and implement?
- **The Native Feature**: Which Interwoven feature did you use, and exactly how does
  it improve the user experience?

### How to Run Locally

[Provide 3-4 clear steps for a judge to run your frontend and connect it to a
local environment if necessary.]
```

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.initia.xyz/llms.txt
> Use this file to discover all available pages before exploring further.

# Initia L1 Networks

## Network Details

<Tabs>
  <Tab title="Mainnet (interwoven-1)">
    | Item                     | Value                                                                                                                                                                                     |
    | ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
    | Chain ID                 | `interwoven-1`                                                                                                                                                                            |
    | REST                     | [https://rest.initia.xyz](https://rest.initia.xyz)                                                                                                                                        |
    | RPC                      | [https://rpc.initia.xyz](https://rpc.initia.xyz)                                                                                                                                          |
    | Genesis Hash (sha256sum) | `f2521b5130e0b26ff47d6155e42e3a0e1e3e1a2676727a317ba34069f3650955`                                                                                                                        |
    | Genesis File             | [https://storage.googleapis.com/init-common-genesis/interwoven-1/genesis.json](https://storage.googleapis.com/init-common-genesis/interwoven-1/genesis.json)                              |
    | Peers                    | `80e8870743458d1a28ce9f9da939e4ddcb7cedfe@34.142.172.124:26656,c02d9c632bcbc7af974399c122eae36a8ed466bb@34.126.106.6:26656,b58e3dacc8c8009514c14e36730b564962028adc@34.124.183.130:26656` |
    | Seeds                    | `80e8870743458d1a28ce9f9da939e4ddcb7cedfe@34.142.172.124:26656`                                                                                                                           |
    | Address Book             | TBA                                                                                                                                                                                       |
  </Tab>

  <Tab title="Testnet (initiation-2)">
    | Item                     | Value                                                                                                                                                            |
    | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
    | Chain ID                 | `initiation-2`                                                                                                                                                   |
    | REST                     | [https://rest.testnet.initia.xyz](https://rest.testnet.initia.xyz)                                                                                               |
    | RPC                      | [https://rpc.testnet.initia.xyz](https://rpc.testnet.initia.xyz)                                                                                                 |
    | Genesis Hash (sha256sum) | `a342fa276722bc90b3bf1ff8cc028102ccd9e897cd7a4ad55161998359a1cde3`                                                                                               |
    | Genesis File             | [https://storage.googleapis.com/init-common-genesis/initiation-2/genesis.json](https://storage.googleapis.com/init-common-genesis/initiation-2/genesis.json)     |
    | Peers                    | `3715cdb41efb45714eb534c3943c5947f4894787@34.143.179.242:26656`                                                                                                  |
    | Seeds                    | `3715cdb41efb45714eb534c3943c5947f4894787@34.143.179.242:26656`                                                                                                  |
    | Address Book             | [https://storage.googleapis.com/init-common-addrbook/initiation-2/addrbook.json](https://storage.googleapis.com/init-common-addrbook/initiation-2/addrbook.json) |
  </Tab>
</Tabs>

## Network Parameters

<Tabs>
  <Tab title="Mainnet (interwoven-1)">
    | Item                     | Value       |
    | ------------------------ | ----------- |
    | Minimum Gas Prices       | 0.015uinit  |
    | Block Gas Limit          | 200,000,000 |
    | Staking Unbonding Period | 21 days     |
    | Governance Voting Period | 7 days      |
  </Tab>

  <Tab title="Testnet (initiation-2)">
    | Item                     | Value       |
    | ------------------------ | ----------- |
    | Minimum Gas Prices       | 0.015uinit  |
    | Block Gas Limit          | 200,000,000 |
    | Staking Unbonding Period | 7 days      |
    | Governance Voting Period | 2 days      |
  </Tab>
</Tabs>

## Endpoints

You can find a number of RPCs, APIs, and gRPCs for the network in the
[Initia Registry](https://github.com/initia-labs/initia-registry) repository.

* [Mainnet (interwoven-1)](https://github.com/initia-labs/initia-registry/blob/main/mainnets/initia/chain.json)
* [Testnet (initiation-2)](https://github.com/initia-labs/initia-registry/blob/main/testnets/initia/chain.json)

## Explorers

<Tabs>
  <Tab title="Mainnet (interwoven-1)">
    * [InitiaScan](https://scan.initia.xyz)
  </Tab>

  <Tab title="Testnet (initiation-2)">
    * [InitiaScan](https://scan.testnet.initia.xyz)
  </Tab>
</Tabs>

## VIP Parameters

<Tabs>
  <Tab title="Mainnet (interwoven-1)">
    | Category           | Parameter                     | Mainnet                  | Explanation                                                                                                                     |
    | ------------------ | ----------------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
    | VIP                | `stage_interval`              | 2 weeks                  | Length of one stage (frequency of esINIT distribution)                                                                          |
    | VIP                | `vesting_period`              | 26 stages                | Total vesting period for esINIT                                                                                                 |
    | VIP                | `minimum_lock_staking_period` | 26 weeks                 | Minimum lock period for an esINIT lock-staking position ("zapping")                                                             |
    | VIP                | `challenge_period`            | 3 days                   | Window during which a score-snapshot challenge may be submitted                                                                 |
    | VIP                | `min_score_ratio`             | 0.5                      | Multiplier applied to the previous stage's score to determine the minimum score required to fully vest esINIT in the next stage |
    | VIP                | `pool_split_ratio`            | 0.2                      | Portion of total rewards directed to the balance pool                                                                           |
    | VIP                | `minimum_eligible_tvl`        | 0                        | Minimum INIT TVL required for whitelisting and eligibility for stage rewards                                                    |
    | VIP                | `maximum_weight_ratio`        | 0.4                      | Maximum share of gauge votes from a single L2, relative to total votes, counted for esINIT distribution                         |
    | VIP (Operator)     | `max_commission_rate`         | 0.25                     | Maximum esINIT commission rate a rollup can set                                                                                 |
    | VIP (TVL manager)  | `snapshot_interval`           | 1 hour                   | Frequency of TVL snapshots for all L2s                                                                                          |
    | VIP (Lock Staking) | `min_lock_period`             | 30 days                  | Minimum lock period for any lock-staking position                                                                               |
    | VIP (Lock Staking) | `max_lock_period`             | 2 years                  | Maximum lock period for all lock-staking positions (including esINIT positions)                                                 |
    | VIP (Lock Staking) | `max_delegation_slot`         | 60                       | Maximum number of unique lock-staking positions per user                                                                        |
    | VIP (gauge vote)   | `cycle_start_time`            | Same as stage start time | Start time of the first gauge-vote cycle                                                                                        |
    | VIP (gauge vote)   | `cycle_interval`              | 2 weeks                  | Length of a gauge-vote cycle                                                                                                    |
    | VIP (gauge vote)   | `voting_period`               | 13 days                  | Duration of the voting window within a cycle                                                                                    |
    | VIP (gauge vote)   | `max_lock_period_multiplier`  | 4                        | Voting-power multiplier for the maximum lock duration                                                                           |
    | VIP (gauge vote)   | `min_lock_period_multiplier`  | 1                        | Voting-power multiplier for the minimum lock duration                                                                           |
    | VIP (gauge vote)   | `pair_multipliers`            | 1 for all pools          | Voting-power multiplier applied to each enshrined liquidity pair                                                                |
  </Tab>

  <Tab title="Testnet (initiation-2)">
    | Category           | Parameter                     | Testnet                  | Explanation                                                                                                                     |
    | ------------------ | ----------------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
    | VIP                | `stage_interval`              | 1 day                    | Length of one stage (frequency of esINIT distribution)                                                                          |
    | VIP                | `vesting_period`              | 26 stages                | Total vesting period for esINIT                                                                                                 |
    | VIP                | `minimum_lock_staking_period` | 1 day                    | Minimum lock period for an esINIT lock-staking position ("zapping")                                                             |
    | VIP                | `challenge_period`            | none                     | Window during which a score-snapshot challenge may be submitted                                                                 |
    | VIP                | `min_score_ratio`             | 0.5                      | Multiplier applied to the previous stage's score to determine the minimum score required to fully vest esINIT in the next stage |
    | VIP                | `pool_split_ratio`            | 0.5                      | Portion of total rewards directed to the balance pool                                                                           |
    | VIP                | `minimum_eligible_tvl`        | 0                        | Minimum INIT TVL required for whitelisting and eligibility for stage rewards                                                    |
    | VIP                | `maximum_weight_ratio`        | 1                        | Maximum share of gauge votes from a single L2, relative to total votes, counted for esINIT distribution                         |
    | VIP (Operator)     | `max_commission_rate`         | none                     | Maximum esINIT commission rate a rollup can set                                                                                 |
    | VIP (TVL manager)  | `snapshot_interval`           | 4 hours                  | Frequency of TVL snapshots for all L2s                                                                                          |
    | VIP (Lock Staking) | `min_lock_period`             | 12 hours                 | Minimum lock period for any lock-staking position                                                                               |
    | VIP (Lock Staking) | `max_lock_period`             | 6 days                   | Maximum lock period for all lock-staking positions (including esINIT positions)                                                 |
    | VIP (Lock Staking) | `max_delegation_slot`         | 50                       | Maximum number of unique lock-staking positions per user                                                                        |
    | VIP (gauge vote)   | `cycle_start_time`            | Same as stage start time | Start time of the first gauge-vote cycle                                                                                        |
    | VIP (gauge vote)   | `cycle_interval`              | 1 day                    | Length of a gauge-vote cycle                                                                                                    |
    | VIP (gauge vote)   | `voting_period`               | 23 hours                 | Duration of the voting window within a cycle                                                                                    |
    | VIP (gauge vote)   | `max_lock_period_multiplier`  | 4                        | Voting-power multiplier for the maximum lock duration                                                                           |
    | VIP (gauge vote)   | `min_lock_period_multiplier`  | 1                        | Voting-power multiplier for the minimum lock duration                                                                           |
    | VIP (gauge vote)   | `pair_multipliers`            | 1 for all pairs          | Voting-power multiplier applied to each enshrined liquidity pair                                                                |
  </Tab>
</Tabs>
