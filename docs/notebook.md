## Notebook experience

If you want to perform local adhoc operations (tests, benchmark…) on warren with a notebook,
you can deploy the stack along with a jupyter notebook server. You can start it with the rest of the stack by doing :
`docker compose up`

You are then able to access the jupyter UI, by using the link provided in the logs of the notebook service : 

`http://127.0.0.1:8888/lab?token=...`