# FreeSWITCH Operations Guide

> **Last Updated**: 2026-01-20
> **Related**: [FreeSWITCH Architecture](./freeswitch-architecture.md) | [Configuration Reference](./freeswitch-configuration-reference.md)

This guide covers day-to-day operations, monitoring, and troubleshooting of FreeSWITCH deployments.

## Table of Contents

1. [Service Management](#service-management)
2. [CLI Operations](#cli-operations)
3. [Monitoring & Metrics](#monitoring--metrics)
4. [Troubleshooting Guide](#troubleshooting-guide)
5. [Common Operations](#common-operations)
6. [Performance Tuning](#performance-tuning)
7. [Backup & Recovery](#backup--recovery)

---

## Service Management

### Systemd Commands

```bash
# Start FreeSWITCH
sudo systemctl start freeswitch

# Stop FreeSWITCH
sudo systemctl stop freeswitch

# Restart FreeSWITCH (full restart)
sudo systemctl restart freeswitch

# Reload configuration (graceful)
sudo systemctl reload freeswitch

# Check status
sudo systemctl status freeswitch

# Enable auto-start on boot
sudo systemctl enable freeswitch

# Disable auto-start
sudo systemctl disable freeswitch

# View service logs
sudo journalctl -u freeswitch -f

# View logs since last boot
sudo journalctl -u freeswitch -b

# View last 100 lines
sudo journalctl -u freeswitch -n 100
```

### Container Operations (Docker/Kubernetes)

```bash
# Docker - View logs
docker logs -f freeswitch-container

# Docker - Execute CLI
docker exec -it freeswitch-container fs_cli

# Kubernetes - View logs
kubectl logs -f deployment/freeswitch -n voice

# Kubernetes - Execute CLI
kubectl exec -it deployment/freeswitch -n voice -- fs_cli

# Kubernetes - Get pod status
kubectl get pods -n voice -l app=freeswitch
```

---

## CLI Operations

### Connecting to FreeSWITCH CLI

```bash
# Local connection
fs_cli

# Remote connection
fs_cli -H <hostname> -P 8021 -p ClueCon

# Execute single command
fs_cli -x "show channels"

# Execute multiple commands from file
fs_cli -x "$(cat commands.txt)"
```

### Essential CLI Commands

#### System Status

```bash
# Overall status
show status

# Show channels (active calls)
show channels
show channels count

# Show calls (A-leg and B-leg pairs)
show calls
show calls count

# Show registrations
show registrations

# Show modules
show modules

# Show codec
show codec

# Show application
show application

# Memory status
status
```

#### Sofia (SIP) Commands

```bash
# Sofia status - all profiles
sofia status

# Sofia status - specific profile
sofia status profile internal1
sofia status profile external1

# Gateway status
sofia status gateway <gateway_name>

# Flush registrations
sofia profile internal1 flush_inbound_reg

# Restart profile (preserves calls)
sofia profile internal1 restart

# Restart profile (drops calls)
sofia profile internal1 stop
sofia profile internal1 start

# Enable/Disable SIP tracing
sofia profile internal1 siptrace on
sofia profile internal1 siptrace off

# Global SIP trace
sofia global siptrace on
sofia global siptrace off

# Sofia log level
sofia loglevel all 9
sofia loglevel all 0

# Reload gateway
sofia profile external1 killgw <gateway_name>
sofia profile external1 rescan

# Register gateway manually
sofia profile external1 register <gateway_name>
```

#### Channel Management

```bash
# List all channels
show channels

# Get channel details by UUID
uuid_dump <uuid>

# Get specific variable
uuid_getvar <uuid> <variable>

# Set variable on channel
uuid_setvar <uuid> <variable> <value>

# Kill a channel
uuid_kill <uuid>

# Kill with specific cause
uuid_kill <uuid> NORMAL_CLEARING
uuid_kill <uuid> USER_BUSY

# Transfer a channel
uuid_transfer <uuid> <destination> [dialplan] [context]

# Bridge two channels
uuid_bridge <uuid1> <uuid2>

# Record a channel
uuid_record <uuid> start <filename>
uuid_record <uuid> stop <filename>

# Park a channel
uuid_park <uuid>

# Break out of application
uuid_break <uuid>

# Send DTMF
uuid_send_dtmf <uuid> <digits>

# Broadcast audio
uuid_broadcast <uuid> <path> [aleg|bleg|both]
```

#### Conference Commands

```bash
# List all conferences
conference list

# List members in conference
conference <name> list

# Kick member
conference <name> kick <member_id>
conference <name> kick all

# Mute/Unmute
conference <name> mute <member_id>
conference <name> unmute <member_id>
conference <name> mute all
conference <name> unmute all

# Lock/Unlock conference
conference <name> lock
conference <name> unlock

# Start/Stop recording
conference <name> record <path>
conference <name> norecord

# Play file to conference
conference <name> play <path>
conference <name> play <path> async

# Stop playback
conference <name> stop
```

#### Configuration & Reloading

```bash
# Reload XML configuration
reloadxml

# Reload specific module
reload mod_sofia
reload mod_lcr
reload mod_conference

# Unload module
unload mod_xyz

# Load module
load mod_xyz

# Reload ACLs
acl reloadxml

# Check if module exists
module_exists mod_sofia
```

#### Logging & Debugging

```bash
# Set console log level
console loglevel debug
console loglevel info
console loglevel warning
console loglevel err

# Available levels: 0-7
# 0 = CONSOLE, 1 = ALERT, 2 = CRIT, 3 = ERR
# 4 = WARNING, 5 = NOTICE, 6 = INFO, 7 = DEBUG

# Enable specific log
fsctl debug_level 7

# Sofia debug
sofia loglevel all 9

# XML CURL debug
xml_curl debug on
xml_curl debug off
```

---

## Monitoring & Metrics

### Key Metrics to Monitor

| Metric | Command | Alert Threshold |
|--------|---------|-----------------|
| Active Channels | `show channels count` | > 80% max-sessions |
| Sessions/Second | `show status` | > 80% sps limit |
| Sofia Profile Status | `sofia status` | Any profile not RUNNING |
| Registration Count | `show registrations count` | Sudden drops |
| Memory Usage | `show status` | Continuous growth |
| CPU Usage | System metrics | > 70% per core |
| Call Failure Rate | CDR analysis | > 5% ASR drop |

### Health Check Script

```bash
#!/bin/bash
# freeswitch-health.sh

HEALTHY=true
OUTPUT=""

# Check if FreeSWITCH is running
if ! pgrep -x freeswitch > /dev/null; then
    OUTPUT="${OUTPUT}FreeSWITCH process not running\n"
    HEALTHY=false
fi

# Check ESL connectivity
if ! echo "api status" | timeout 2 nc localhost 8021 > /dev/null 2>&1; then
    OUTPUT="${OUTPUT}ESL port 8021 not responding\n"
    HEALTHY=false
fi

# Check Sofia profiles
SOFIA_STATUS=$(fs_cli -x "sofia status" 2>/dev/null)
if echo "$SOFIA_STATUS" | grep -q "FAILED\|DOWN"; then
    OUTPUT="${OUTPUT}Sofia profile(s) down\n"
    HEALTHY=false
fi

# Check active channels vs limit
CHANNELS=$(fs_cli -x "show channels count" 2>/dev/null | grep -oP '^\d+')
MAX_SESSIONS=$(fs_cli -x "global_getvar max-sessions" 2>/dev/null || echo "1500")
if [ "$CHANNELS" -gt $((MAX_SESSIONS * 80 / 100)) ]; then
    OUTPUT="${OUTPUT}Channel count above 80% threshold\n"
    HEALTHY=false
fi

if $HEALTHY; then
    echo "HEALTHY"
    exit 0
else
    echo -e "UNHEALTHY:\n$OUTPUT"
    exit 1
fi
```

### Prometheus Metrics (via mod_prometheus or ESL)

```yaml
# Example metrics that should be exposed
freeswitch_channels_active
freeswitch_calls_active
freeswitch_sessions_total
freeswitch_sessions_per_second
freeswitch_registrations_active
freeswitch_sofia_profile_status
freeswitch_memory_usage_bytes
freeswitch_uptime_seconds
```

---

## Troubleshooting Guide

### Issue: Sofia Profile Won't Start

**Symptoms:**
- Profile shows as "DOWN" in `sofia status`
- Calls fail to connect

**Diagnosis:**
```bash
# Check profile status
sofia status profile internal1

# Check for port conflicts
netstat -tlnp | grep 5061

# Check logs
fs_cli -x "console loglevel debug"
sofia profile internal1 start
```

**Common Causes:**
1. **Port already in use** - Another process using the port
2. **IP binding issue** - IP address not available
3. **TLS certificate issue** - Invalid or missing certificate

**Solutions:**
```bash
# Kill conflicting process
sudo fuser -k 5061/tcp

# Fix IP binding (vars.xml)
<X-PRE-PROCESS cmd="set" data="local_ip_v4=192.168.1.100"/>

# Check TLS certificates
ls -la /etc/freeswitch/tls/
openssl x509 -in /etc/freeswitch/tls/agent.pem -text -noout
```

### Issue: Calls Dropping After Answer

**Symptoms:**
- Calls connect but drop after a few seconds
- One-way or no audio

**Diagnosis:**
```bash
# Enable RTP debugging
uuid_debug_media <uuid> read on
uuid_debug_media <uuid> write on

# Check RTP stats
uuid_media_stats <uuid>

# Check NAT settings
uuid_dump <uuid> | grep rtp
```

**Common Causes:**
1. **NAT traversal issues** - RTP packets can't reach endpoint
2. **Firewall blocking RTP** - UDP ports blocked
3. **Codec mismatch** - No common codec negotiated

**Solutions:**
```bash
# Configure external RTP IP (sip_profiles/internal1.xml)
<param name="ext-rtp-ip" value="PUBLIC_IP"/>

# Ensure firewall allows RTP range
iptables -A INPUT -p udp --dport 16384:32768 -j ACCEPT

# Force codec (dialplan)
<action application="set" data="absolute_codec_string=PCMA"/>
```

### Issue: XML CURL Timeouts

**Symptoms:**
- Calls fail with "no route found"
- Slow call setup
- Log shows curl timeouts

**Diagnosis:**
```bash
# Enable XML CURL debug
xml_curl debug on

# Test API endpoint manually
curl -v -X POST http://api-host:8080/freeswitch/dialplan.xml \
  -d "section=dialplan&hostname=fs01"

# Check network connectivity
ping api-host
telnet api-host 8080
```

**Common Causes:**
1. **API server down** - Service not running
2. **Network latency** - Slow response times
3. **DNS issues** - Cannot resolve hostname

**Solutions:**
```bash
# Increase timeout (xml_curl.conf.xml)
<param name="timeout" value="30"/>
<param name="connect-timeout" value="10"/>

# Use IP instead of hostname
<param name="gateway-url" value="http://10.0.0.100:8080/freeswitch/dialplan.xml"/>

# Add fallback
<param name="gateway-url" value="http://api-host:8080/freeswitch/dialplan.xml"/>
<param name="gateway-url-failover" value="http://api-backup:8080/freeswitch/dialplan.xml"/>
```

### Issue: Registration Failures

**Symptoms:**
- Users can't register
- Log shows "401 Unauthorized"

**Diagnosis:**
```bash
# Check registrations
show registrations

# Enable auth logging
sofia profile internal1 siptrace on

# Check directory lookup
xml_curl debug on
```

**Common Causes:**
1. **Wrong credentials** - Password mismatch
2. **Domain mismatch** - User registering to wrong domain
3. **Directory lookup failure** - XML CURL not returning user

**Solutions:**
```bash
# Check user in directory
curl -X POST http://api:8080/freeswitch/directory.xml \
  -d "section=directory&domain=example.com&user=1001"

# Force domain (sip_profiles/internal1.xml)
<param name="force-register-domain" value="example.com"/>

# Check ACLs
fs_cli -x "acl domains 192.168.1.100"
```

### Issue: High Memory Usage

**Symptoms:**
- Memory continuously growing
- Eventually crashes or OOM killer activates

**Diagnosis:**
```bash
# Check current memory
show status

# Monitor memory over time
watch -n 5 'fs_cli -x "show status" | grep -i mem'

# Check for stuck channels
show channels
```

**Common Causes:**
1. **Memory leak in module** - Bug in custom module
2. **Stuck channels** - Calls not properly terminated
3. **Cache buildup** - Too many cached objects

**Solutions:**
```bash
# Kill stuck channels
fs_cli -x "hupall normal_clearing"

# Flush registrations
sofia profile internal1 flush_inbound_reg

# Restart FreeSWITCH (if needed)
sudo systemctl restart freeswitch

# Enable crash protection (switch.conf.xml)
<param name="crash-protection" value="true"/>
```

---

## Common Operations

### Adding a New SIP Trunk

1. **Create gateway configuration:**
```xml
<!-- /etc/freeswitch/sip_profiles/external/carrier_name.xml -->
<include>
  <gateway name="carrier_name">
    <param name="realm" value="sip.carrier.com"/>
    <param name="proxy" value="sip.carrier.com:5060"/>
    <param name="username" value="your_username"/>
    <param name="password" value="your_password"/>
    <param name="register" value="true"/>
    <param name="expire-seconds" value="300"/>
    <param name="retry-seconds" value="30"/>
    <param name="caller-id-in-from" value="true"/>
  </gateway>
</include>
```

2. **Reload Sofia profile:**
```bash
fs_cli -x "sofia profile external1 rescan"
```

3. **Verify gateway status:**
```bash
fs_cli -x "sofia status gateway carrier_name"
```

### Updating Dialplan Rules

1. **Modify XML configuration** or update via Core API
2. **Reload XML:**
```bash
fs_cli -x "reloadxml"
```
3. **Test new dialplan:**
```bash
fs_cli -x "expand dialplan_test 18005551234"
```

### Taking FreeSWITCH Out of Rotation

```bash
# Stop new calls (keep existing)
fs_cli -x "fsctl pause"

# Wait for calls to complete
while [ $(fs_cli -x "show channels count" | grep -oP '^\d+') -gt 0 ]; do
    sleep 5
done

# Now safe to restart
sudo systemctl restart freeswitch

# Resume accepting calls
fs_cli -x "fsctl resume"
```

### Emergency Call Termination

```bash
# Kill all active calls
fs_cli -x "hupall normal_clearing"

# Kill calls on specific profile
fs_cli -x "sofia profile internal1 killall"

# Kill specific gateway calls
fs_cli -x "sofia profile external1 killgw gateway_name"
```

---

## Performance Tuning

### System-Level Tuning

```bash
# /etc/sysctl.conf additions
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.core.rmem_default = 262144
net.core.wmem_default = 262144
net.ipv4.udp_mem = 65536 131072 262144
net.core.netdev_max_backlog = 65536
net.ipv4.tcp_max_syn_backlog = 65536

# File descriptor limits
# /etc/security/limits.conf
freeswitch    soft    nofile    999999
freeswitch    hard    nofile    999999
```

### FreeSWITCH Tuning

```xml
<!-- switch.conf.xml -->
<param name="max-sessions" value="3000"/>
<param name="sessions-per-second" value="256"/>

<!-- Disable unnecessary logging -->
<param name="loglevel" value="warning"/>
```

### Profile Tuning

```xml
<!-- sip_profiles/internal1.xml -->
<param name="log-level" value="0"/>
<param name="debug" value="0"/>
<param name="sip-trace" value="no"/>
```

---

## Backup & Recovery

### Configuration Backup

```bash
#!/bin/bash
# backup-freeswitch.sh

BACKUP_DIR="/backup/freeswitch"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR/$DATE

# Backup configuration
tar -czf $BACKUP_DIR/$DATE/config.tar.gz /etc/freeswitch/

# Backup recordings (if needed)
tar -czf $BACKUP_DIR/$DATE/recordings.tar.gz /var/lib/freeswitch/recordings/

# Backup voicemail
tar -czf $BACKUP_DIR/$DATE/voicemail.tar.gz /var/lib/freeswitch/voicemail/

# Cleanup old backups (keep last 7 days)
find $BACKUP_DIR -type d -mtime +7 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR/$DATE"
```

### Configuration Restore

```bash
#!/bin/bash
# restore-freeswitch.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

# Stop FreeSWITCH
sudo systemctl stop freeswitch

# Backup current config
mv /etc/freeswitch /etc/freeswitch.old

# Restore from backup
tar -xzf $BACKUP_FILE -C /

# Fix permissions
chown -R freeswitch:freeswitch /etc/freeswitch

# Start FreeSWITCH
sudo systemctl start freeswitch

echo "Restore completed"
```

### Database Recovery (LCR)

```bash
# Export LCR data
pg_dump -U postgres freeswitch_lcr > lcr_backup.sql

# Restore LCR data
psql -U postgres freeswitch_lcr < lcr_backup.sql

# Reload LCR module
fs_cli -x "reload mod_lcr"
```

---

## Related Documentation

- [FreeSWITCH Architecture](./freeswitch-architecture.md)
- [Configuration Reference](./freeswitch-configuration-reference.md)
- [SIP Trunk Configuration](./sip-trunk-configuration.md)
- [Call Routing Rules](./call-routing-rules.md)
