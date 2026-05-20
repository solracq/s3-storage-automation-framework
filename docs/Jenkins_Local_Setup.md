# Local Jenkins Setup on macOS

This guide is tailored for a local Jenkins controller that can run this S3 automation project and other projects on the same machine.

## Why this approach

For this repository, running Jenkins directly on your Mac is simpler than running the Jenkins controller in Docker.

- This project already uses `docker compose` with bind mounts.
- A native local Jenkins process can call Docker Desktop and local files without extra container-to-host path mapping.
- It stays reusable for other local projects too.

## Local machine specs

- macOS `26.4.1`
- Java `21.0.5`
- Docker CLI and Docker Compose installed

**Note:** Jenkins LTS `2.555.1` (released April 15, 2026) requires Java 21 or Java 25.

## 1. Create a local Jenkins home

```bash
mkdir -p "$HOME/jenkins-local/home"
mkdir -p "$HOME/jenkins-local/war"
mkdir -p "$HOME/jenkins-local/logs"
```

## 2. Download Jenkins LTS

As of May 20, 2026, the current Jenkins LTS is `2.555.1`.

```bash
curl -L https://get.jenkins.io/war-stable/2.555.1/jenkins.war \
  -o "$HOME/jenkins-local/war/jenkins.war"
```

## 3. Start Docker Desktop

Open Docker Desktop and wait until it shows as running. Jenkins will need it later for this repository because the test stack uses `docker compose`.

Quick check:

```bash
docker ps
docker compose version
```

## 4. Start Jenkins

```bash
export JENKINS_HOME="$HOME/jenkins-local/home"
nohup java -jar "$HOME/jenkins-local/war/jenkins.war" --httpPort=8080 \
  > "$HOME/jenkins-local/logs/jenkins.out" 2>&1 &
echo $! > "$HOME/jenkins-local/jenkins.pid"
```

## 5. Unlock Jenkins

Wait around 20-60 seconds, then get the initial admin password:

```bash
cat "$HOME/jenkins-local/home/secrets/initialAdminPassword"
```

Open:

```text
http://localhost:8080
```

Paste the password into the Unlock Jenkins screen.

## 6. Complete the first-run wizard

Choose:

- `Install suggested plugins`

Then:

- Create your admin user
- Set the Jenkins URL to `http://localhost:8080/`

## 7. Add the plugins needed for this project

Go to `Manage Jenkins` -> `Plugins` and install:

- `Docker Pipeline`
- `JUnit`
- `Pipeline: Stage View`
- `Pipeline Graph View`
- `Git`
- `Credentials Binding`
- `Workspace Cleanup`

Note:

- Use `Pipeline Graph View` and `Pipeline: Stage View` instead of Blue Ocean.
- Jenkins documentation notes Blue Ocean is deprecated in July 2026.

## 8. Verify Jenkins can use local tools

Create a small test Pipeline job and run:

```groovy
pipeline {
    agent any
    stages {
        stage('Check Tooling') {
            steps {
                sh 'java -version'
                sh 'docker --version'
                sh 'docker compose version'
            }
        }
    }
}
```

If that passes, your local Jenkins controller is ready for this repository.

## 9. Stop Jenkins

```bash
kill "$(cat "$HOME/jenkins-local/jenkins.pid")"
```

## 10. Start Jenkins again later

```bash
export JENKINS_HOME="$HOME/jenkins-local/home"
nohup java -jar "$HOME/jenkins-local/war/jenkins.war" --httpPort=8080 \
  > "$HOME/jenkins-local/logs/jenkins.out" 2>&1 &
echo $! > "$HOME/jenkins-local/jenkins.pid"
```

**How to kill Jenkins when it hangs or becomes unresponsive**
```bash
pkill -TERM -f 'jenkins.war'
pkill -TERM -f 'git fetch'
pkill -TERM -f 'ssh .*github.com'

sleep 2

pkill -KILL -f 'jenkins.war'
pkill -KILL -f 'git fetch'
pkill -KILL -f 'ssh .*github.com'
```

Then, re-start it.
```bash
kill "$(cat "$HOME/jenkins-local/jenkins.pid")"

export JENKINS_HOME="$HOME/jenkins-local/home"
nohup java -jar "$HOME/jenkins-local/war/jenkins.war" --httpPort=8080 \
  > "$HOME/jenkins-local/logs/jenkins.out" 2>&1 &
echo $! > "$HOME/jenkins-local/jenkins.pid"
```
