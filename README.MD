# ABOUT THIS REPO
This microservice is used to dispatch encoded messages among active endpoints within the related project (see [Project Summary](#project-summary)).

# DEPENDENCIES
- [RabbitMQ](https://www.rabbitmq.com/)
- MySQL database

# SETUP
- Install the dependencies listed in ```requirements.txt```
- Make copy of the ```config.example.ini``` and name it ```config.ini```
- Fill the database connection requisites in the ```DATABASE``` section of the ```config.ini``` file
- Fill the RabbitMQ connection requisites in the ```RABBIT``` section of the ```config.ini``` file 
- Change queue names in the ```APP``` section of the ```config.ini``` file if necessary (see [Queues](#queues))

# QUEUES
| Queue Name       | Description                                     |
|------------------|-------------------------------------------------|
| queue_dispatcher | Queue from which incoming messages are received |
| queue_email_bz   | Queue for the SMTP BZ endpoint                  |
| queue_tg_message | Queue for the Telegram endpoint                 |

# PROJECT SUMMARY
This project is a set of microservices for distribution of an initial message with all kinds of services:
Telegram, E-mail or any other service as deemed necessary, including plain HTTP requests.

The idea of the project is to allow a user to set up a project with desirable endpoints and to send a message only once
to distribute it, including any media attached thereto.

The project utilizes [RabbitMQ](https://www.rabbitmq.com/) for message distribution.

The project consists of a receiver microservice to encode initial text and attachments into JSON
and a dispatcher microservice to push the message into project-related queues for further processing:

```
                                              --> endpoint microservice #1
                                              |    
incoming message --> receiver --> dispatcher ---> endpoint microservice #2
                                              |
                                              --> endpoint microservice #3 
```

The final distribution is performed by endpoint microservices, each implemented depending on capabilities of the
system used. Use of [RabbitMQ](https://www.rabbitmq.com/) allows to deploy as many clones of an endpoint microservice as
required in case if such channel is used extensively.

[Dashboard]()

Other microservices:

- [Receiver]()
- [Dispatcher]()
- [SMTP BZ Sender]()
- [Telegram Sender]()