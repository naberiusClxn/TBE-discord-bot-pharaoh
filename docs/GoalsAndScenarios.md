# Project Goals and Test Scenarios

## Project Goals

1. **User Access Management**
   - Granting server access and managing access to voice channels.
   - Restricting user access to specific channels.

2. **Punishment System**
   - Implementing temporary and permanent restrictions (mute, warn, ban).
   - Removing or adjusting applied punishments.

3. **Giveaway and Event Organization**
   - Conducting giveaways among users.
   - Issuing server currency and experience tokens.

4. **Experience and Tokens System**
   - Issuing and deducting experience tokens for users.
   
5. **Financial System**
   - Checking user balance.
   - Working with the marketplace and item storage.

6. **Database Integration**
   - Storing user information, statuses, punishments, balances, and purchases.
   
7. **Access Levels System**
   - Dividing commands into administrative and user commands.
   - Restricting access to administrative commands.

---

## Test Scenarios

### 1. User Access Management
**Scenario 1.1:** Granting access to the server
1. Send the command `/skip @user`.
2. Verify that the user gains access to voice channels.

**Scenario 1.2:** Restricting user access
1. Send the command `/lock @user`.
2. Verify that the user can only stay in one channel.

### 2. Punishment System
**Scenario 2.1:** Muting a user
1. Send the command `/mute @user 10m spam`.
2. Verify that the user cannot speak in voice channels for 10 minutes.

**Scenario 2.2:** Unmuting a user
1. Send the command `/unmute @user`.
2. Verify that the user can speak again.

**Scenario 2.3:** Issuing a warning
1. Send the command `/warn @user rule violation`.
2. Verify that the user receives a warning.

**Scenario 2.4:** Removing a warning
1. Send the command `/unwarn @user`.
2. Verify that the warning is removed.

**Scenario 2.5:** Banning a user
1. Send the command `/ban @user 1d rule violation`.
2. Verify that the user cannot enter the server for 1 day.

### 3. Giveaway Organization
**Scenario 3.1:** Creating a giveaway
1. Send the command `/roll 10m Nitro`.
2. Verify that the giveaway starts and users can participate.

**Scenario 3.2:** Manually selecting a winner
1. Send the command `/rolls`.
2. Verify that the bot announces a winner.

### 4. Experience and Tokens
**Scenario 4.1:** Issuing an experience token
1. Send the command `/givet @user`.
2. Verify that the token is added to the user profile.

**Scenario 4.2:** Removing an experience token
1. Send the command `/taket @user`.
2. Verify that the token is removed from the user profile.

### 5. Balance and Marketplace
**Scenario 5.1:** Checking balance
1. Send the command `/balance`.
2. Verify that the user's current balance is displayed.

**Scenario 5.2:** Purchasing an item from the marketplace
1. Send the command `/market` and select an item.
2. Verify that the item is deducted from the balance and added to storage.

**Scenario 5.3:** Checking items in storage
1. Send the command `/storage`.
2. Verify that all acquired items are displayed.

### 6. Access Level Verification
**Scenario 6.1:** A user attempts to execute an admin command
1. A regular user sends the command `/ban @user`.
2. Verify that the bot rejects the command with a permission error.

### 7. Database Verification
**Scenario 7.1:** Saving user data
1. Execute the command `/warn @user`.
2. Restart the bot.
3. Verify that the warning still appears in the user's profile.

**Scenario 7.2:** Updating data upon balance changes
1. Execute the command `/agive @user 100`.
2. Verify that the balance is updated.
3. Restart the bot.
4. Verify that the balance remains unchanged.

---

This list covers the core functionality of the bot and allows QA to validate its correctness.