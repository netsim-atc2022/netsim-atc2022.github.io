### Simulator

This page describes an open-source software tool for the research paper
described on the [home page](/).

A primary contribution of our paper is the design and implementation of a novel
simulation architecture and a practical network simulator tool. The simulator
tool has been released as open-source software and has been merged into
[Shadow](https://shadow.github.io), an open-source network simulation project
[hosted on Github](https://github.com/shadow/shadow). Shadow uses our simulator
design as of `v2.0.0-pre.0` and later.

Because Shadow is actively developed at the time of this writing, it has
continued to improve and mature after the conclusion of our research project and
publication of our paper. Therefore, there are multiple versions to consider:

- If your goal is to use our tool for your own research, then you will likely want
  to download the _latest and greatest_ version of Shadow following the latest
  guidance. We refer you to [the Shadow website](https://shadow.github.io) and
  [the Shadow Github page](https://github.com/shadow/shadow).

- [Shadow at tag `v2.0.0-pre.4`](https://github.com/shadow/shadow/tree/v2.0.0-pre.4)
  contains the design described in the paper, and this is the version we used to
  carry out our experiments. `v2.0.0-pre.4` can be installed as described in
  [the corresponding documentation](https://github.com/shadow/shadow/tree/v2.0.0-pre.4/docs)
  or using Docker following our instructions below. `v2.0.0-pre.4` is not the
  most recent version of Shadow, so you should only use it if you are trying to
  precisely reproduce the results in our paper.

### Docker

Our paper uses [Shadow at tag
`v2.0.0-pre.4`](https://github.com/shadow/shadow/tree/v2.0.0-pre.4), which
requires the `pidfd_open` syscall: this syscall was added in Linux kernel v5.3
(published on 2019-09-15). Please ensure that your docker host machine is
running Linux v5.3 or later, e.g., using `uname -a`. (The lastest version
of Shadow from [the Shadow Github page](https://github.com/shadow/shadow) does
not use `pidfd_open` and does not have this requirement.)

To install Shadow `v2.0.0-pre.4` using Docker, first 
[install Docker](https://docs.docker.com/get-docker/) and `git`,
and then run these commands:

```
git clone https://github.com/netsim-atc2022/netsim-atc2022.github.io.git
cd netsim-atc2022.github.io/setup
bash build_simulator.sh
```

Once the above commands complete successfully, you should be able to get a
shell in a container with:

```
docker run \
    --privileged \
    --tmpfs /dev/shm:rw,nosuid,nodev,exec,size=10g \
    -it netsim:simulator \
    bash
```

Once inside the container, you can check that the installation is working:

```
/phantom/bin/shadow --help
/phantom/bin/shadow /root/test.yaml > shadow.log
cat shadow.data/hosts/client1/client1.curl.1000.stdout
```

You should see an HTML directory listing similar to the following:

```
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>Directory listing for /</title>
</head>
<body>
<h1>Directory listing for /</h1>
<hr>
<ul>
<li><a href="server.python3.8.1000.shimlog">server.python3.8.1000.shimlog</a></li>
<li><a href="server.python3.8.1000.stderr">server.python3.8.1000.stderr</a></li>
<li><a href="server.python3.8.1000.stdout">server.python3.8.1000.stdout</a></li>
</ul>
<hr>
</body>
</html>
```

Type `exit` to leave the container.
