# part 1 - Design

### 1.Explain your choice of the application domain and generic types of data to be supported and technologies for mysimbdp-coredms. Explain your assumption about the tenant data sources and how one could get data from the sources. Explain under which situations/assumptions, your platform serves for big data workload. (1 point)
I chose to use Nifi for the data ingestion and transformation because it is easy to use and scalable. it also supports real-time data processing. I chose to use CockroachDB for storing data. It is built with a distributed and resilient architecture that ensures data availability and fault tolerance. It also provides s trong consistency across the transactions. mysimbdp-coredms supports string, integer, float, and datetime. My assumption about the tenant dat sources is that they will upload csv files in which the first line is the header. A CSV file can contain a number of rows. If many tenants upload csv files at the same time for big data analysis, then it can easily become a big data workload.  

### 2. Design and explain the interactions among main platform components in your architecture of mysimbdp. Explain how would the data from the sources will be ingested into the platform. Explain which would be the third parties (services/infrastructures) that you do not develop for your platform. (1 point)
First, the user uploads a csv file. The post request will be handled by the rest server, The server will create a table in the database based on the headers of the csv file and store the csv file in the local directories called 'uploads/csv'. The uploaded csv files will be picked up by Nifi and will be inserted to CockroachDB. 

### 3. Explain a configuration of a cluster of nodes for mysimbdp-coredms so that you prevent a singlepoint-of-failure problem for mysimbdp-coredms for your tenants. (1 point)
A cluster of three cockroachDB nodes are configured in the local environment (more than that would cause using all the cpu and memory resources). CockroachDB creates a three replicas of a node. if one node dies, then data will be rebalanced among the other two nodes.

### 4. You decide a pre-defined level of data replication for your tenants/customers. Explain the level of replication in your design, how many nodes are needed in the deployment of mysimbdp-coredms for your choice so that this component can work property (e.g., the system still supports redundancy in the case of a failure of a node). (1 point)
Three replicas of a node will be sufficient. In the deployment, 4 or 5 nodes will be needed. 

### 5. Consider the platform data center, the tenant data source locations and the network between them. Explain where would you deploy mysimbdp-dataingest to allow your tenants using mysimbdpdataingest to push data into mysimbdp, based on which assumptions you have. Explain the performance pros and cons of the deployment place, given the posibilities you have. (1 point)

I will deploy the dadtaingest in the same region as the data center. A tenant just need to upload a few files to the server. The server will just need to download the file and respond to the user to inform that that the ingestion is in progress. The advantage of this appraoch is that there is low latency and high bandwidth between the data ingestion and database and also simplifies the network configuration. The disadvantage is that it might reduce the user experience. But, i think its impact would be limited. 

# part 2 - implementation

### 1. Design, implement and explain one example of the data schema/structure for a tenant whose data will be stored into mysimbdp-coredms. (1 point)
Airbnb's listings.csv contains the following columns: 
```
id                                                int64
listing_url                                      object
scrape_id                                         int64
last_scraped                                     object
source                                           object
                                                 ...   
calculated_host_listings_count                    int64
calculated_host_listings_count_entire_homes       int64
calculated_host_listings_count_private_rooms      int64
calculated_host_listings_count_shared_rooms       int64
reviews_per_month                               float64
```
All the rows in the csv file will be stored in a table called _listings_ accordingly. 

### 2. Given the data schema/structure of the tenant (Part 2, Point 1), design a strategy for data partitioning/sharding, explain the goal of the strategy (performance, data regulation and/or what), and explain your implementation for data partitioning/sharding together with your design for replication in Part 1, Point 4, in mysimbdp-coredms. (1 point)

CockroachDB stores data in a monolithic sorted map of key-value pairs. This key-space describes all of the data in the cluster, as well as its location, and is divided into what they call "ranges", which is same as "shard", contiguous chunks of the key-space, so that every key can always be found in a single range.

### 3. Assume that you are the tenant, emulate the data sources with the real selected dataset and write a mysimbdp-dataingest that takes data from your selected sources and stores the data into mysimbdp-coredms. Explain what would be the atomic data element/unit to be stored. Explain possible consistency options for writing data in your mysimdbp-dataingest. (1 point)

currently my ingestion pipeline splits the CSV file if it's too large, for example by 100 rows. That is, it will commit 100 rows each time. atomic unit to be stored would be in this case 100 rows of the csv file. CockroachDB ensures that data is written to other replicas by ensuring that other replicas get the data before confirming that commit has been successful. If the majorify says that it received the data, then it will confirm the commit. 

### 4. Given your deployment environment, measure and show the performance (e.g., response time, throughputs, and failure) of the tests for 1,5, 10, .., n of concurrent mysimbdp-dataingest writing data into mysimbdp-coredms with different speeds/velocities together with the change of the number of nodes of mysimbdp-coredms. Indicate any performance differences due to the choice of consistency options. (1 point)
I had difficult time increasing the number of nodes because of limited resources of CPU and memory on my laptop. So, when i had more than 3 nodes, the docker containers consumed all the available resources and stopped working. So, could not measure the performance of the test. 
### 5. Observing the performance and failure problems when you push a lot of data into mysimbdpcoredms (you do not need to worry about duplicated data in mysimbdp), propose the change of your deployment to avoid such problems (or explain why you do not have any problem with your deployment). (1 point)

For some reason, flows get stuck in the queue before DistributedLoad, which is to load balance the received records to different cockroachDB nodes. i tried to fix the issue by changing the configuration in nifi.properties to increase the load balance max thread count and load balance connections per node, but it didn't work.

I could have instead used the proxy server that load balances the incoming records instead. But, didn't have time to implement it.


# extension
### 1. Using your mysimdbp-coredms, a single tenant can run mysimbdp-dataingest to create many different databases/datasets. The tenant would like to record basic lineage of the ingested data, explain what types of metadata about data lineage you would like to support and how would you do this. Provide one example of a lineage data. (1 point)

### 2. Assume that each of your tenants/users will need a dedicated mysimbdp-coredms. Design the data schema of service information for mysimbdp-coredms that can be published into an existing registry (like ZooKeeper, consul or etcd) so that you can find information about which mysimbdp-coredms is for which tenants/users. (1 point)


### 3. Explain how you would change the implementation of mysimbdp-dataingest (in Part 2) to integrate a service discovery feature (no implementation is required). (1 point)
i will create a cluster of Apache NiFi instances to increase the throughput and to implement retry and failover mechanisms within the data ingestion pipeline to handle cases where Apanche Nifi instance becomes unavailable or unresponsive. The nodes in an Apache NiFi cluster can be managed by Apache ZooKeeper. The Apache NiFi documentation recommends that you run ZooKeeper on either three or five nodes.

### 4. Assume that now only mysimbdp-daas can read and write data into mysimbdp-coredms, how would you change your mysimbdp-dataingest (in Part 2) to work with mysimbdp-daas? (1 point)
To accommodate the new requirement where only mysimbdp-daas is permitted to read and write data into mysimbdp-coredms, I will retain the use of mysimbdp-dataingest for data writing operations initiated by users. However, for data reading operations from mysimbdp-coredms, the API will directly retrieve data from mysimbdp-coredms via mysimbdp-daas. 

### 5. Assume that the platform allows the customer to define which types of data (and) that should be stored in a hot space and which should be stored in a cold space in the mysimbdp-coredms. Provide one example of constraints based on characteristics of data for data in a hot space vs in a cold space. Explain how would you support automatically moving/extracting data from a hot space to a cold space. (1 point)

Data is strategically divided between hot and cold storage spaces based on its access patterns and relevance. For instance, frequently accessed data, such as real-time analytics or operational data, is stored in the hot space to ensure low-latency access and fast response times. Conversely, historical or less frequently accessed data, like past Airbnb prices, is relegated to the cold space.

To automatically manage this data segregation, I would implement a mechanism that evaluates the timestamp of data access. If data remains untouched for a specified duration, it would be identified as suitable for migration to the cold space. This approach optimizes storage efficiency and performance by dynamically adjusting data placement according to its usage patterns