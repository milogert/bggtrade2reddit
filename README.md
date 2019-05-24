# BGG For Trade list -> Reddit table

This small program converts your BGG For Trade list to a nicely formatted Reddit table, including grouping expansions with base games if they exist.

# Running the program

```
source .venv/bin/activate
./main.py your_username
```

# Enhancing output

You can enchance the output by including a tag, followed by a colon, followed by some json in the "Trade Condition" column on BGG. The json must be on a single line and it must be formatted like so:

`bggtrade2reddit:{"key":"value"}`

## Optional keys for enhanced output

* `condition`: (`number`) sets your condition number. Generally out of four or five.
* `price`: (`number`) in USD. TODO: pull request for setting your denomination.
* `extras`: (`string`) any extras you want to call out, for instance "everything sleeved" or "no box".
* `ignore`: (`boolean`) if this is set to `true` then this program will ignore it and not place it in the table.
