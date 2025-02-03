
# Technical Task for the Development of a Bot
**1. Commands for Administrators**
These commands are designed to manage users and their access to various sections of the server.

**1.1. Access Management**

 - /skip – Allows a user to enter the server, granting access to a
   number of public voice channels. 
 - /lock – Limits a user's access to
   only one room, blocking access to other public channels.

**1.2. Punishment Management**

 - /mute [user ID] [reason] [time] – Mutes a user for a certain period
   of time.

 - /unmute [user ID] [reason] [time] – Unmutes a user.

 - /warn [user ID] [reason] [time] – Issues a warning to a user for a limited period of time. /unwarn [user ID] [reason] – Removes a
   warning from a user. 
   -/ban [user ID] [reason] [time] – Bans a user for a certain period of time. /unban [user ID] [reason] – Unbans a user.

**2. Event and Giveaway Commands**
These commands are designed to organize various giveaways, including gifts, currency, and other bonuses.

**2.1. Giveaways and Announcements**
- /roll [time] [reward] – Start a giveaway (e.g. Nitro, points, currency, discounts) among all users on the server.
- /rolls – Immediately assign a winner to the giveaway.
- /rolla [time] [reward] [rooms] – Giveaway among users in the specified rooms. You must specify a list of rooms.
- /agive [user ID] [amount] – Assign server currency to the user.

**3. Third-Party Commands (Experience Tokens)**
These commands are related to the issuance and withdrawal of experience tokens, which are displayed in the user profile.

- /givet [user ID] – Issues a token to the user. The token is not a server currency, but serves as an experience currency displayed in the profile.
- /taket [user ID] – Takes an experience token from the user.

**4. General commands for users**
These commands provide information about the user's profile and their interaction with the server.

**4.1. User profile**
- /profile [user ID] or /profile [user ID] – Opens the user profile. If no ID is specified, the current user's profile is displayed.

**4.2. User balance**
- /balance or /balance – Shows the current user's server balance.
!balance or !$ – Quickly display the balance in the chat.

**4.3. Getting experience tokens**
- /workt – Request to issue an experience token.

**4.4. Store**
- /market – Opens a store where users can spend server currency on various goods and privileges. Initially, 6 items are offered based on pictures (will be expanded later).

**4.5. Item Storage**
- /storage – Storage space for items and goodies won or purchased. The command will be used to receive items or perform other operations with them (for example, earning).

**5. Features and Additional Requirements**
Currency System: At the moment, the decision on the accrual of server currency has not yet been made. This will require further discussion and implementation of appropriate algorithms.
Database: The bot will require integration with a database to operate, which will store information about users, their punishments, balances, items, and other elements interacting with the bot.
Access Levels: Commands for administrators must be protected from unauthorized use, requiring execution rights.

**6. Conclusion**
This Technical Assignment describes the main commands and functions of the bot that must be implemented for full functionality. It is expected that the bot will have a flexible system for managing users and their punishments, as well as the ability to organize various events and giveaways. Commands for working with experience tokens and server currency are also provided.

Implementation details, such as the method of currency accrual, may be clarified later in the development process.Technical Task for the Development of a Bot