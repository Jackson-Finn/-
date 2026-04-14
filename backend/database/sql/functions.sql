/* SQLite does not support CREATE FUNCTION in plain SQL scripts.
   Application-side service functions are used in local development.
   For MySQL deployment, introduce stored functions for:
   1. unread notification count
   2. seller average rating
   3. product recommendation score aggregation
*/

