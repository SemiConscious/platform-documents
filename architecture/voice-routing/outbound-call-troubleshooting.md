# Outbound Call Troubleshooting Guide

## Overview

This guide provides troubleshooting steps for common outbound call issues in the Natterbox voice platform.

---

## Quick Diagnosis Checklist

### Pre-Call Checks

- [ ] User has valid Natterbox account and device registered
- [ ] Destination number is in valid E.164 format
- [ ] Organization has active carriers configured
- [ ] LCR profile exists and has routes for destination
- [ ] User's caller ID is validated and allowed
- [ ] Carrier gateways are healthy

### Call Progress Checks

- [ ] SIP INVITE sent to carrier
- [ ] 100 Trying received from carrier
- [ ] 180/183 received (ringing/progress)
- [ ] 200 OK received (answered)
- [ ] ACK sent successfully
- [ ] Media (RTP) flowing bidirectionally

---

## Common Issues and Solutions

### 1. Call Fails Immediately - NO_ROUTE_DESTINATION

**Symptoms:**
- Call fails instantly with "No route to destination" error
- SIP 404 response
- Q.850 cause code 3

**Possible Causes:**

| Cause | Solution |
|-------|----------|
| Invalid destination format | Verify E.164 format (+country code + number) |
| No LCR routes for prefix | Add routes for destination prefix |
| All routes disabled | Enable routes in LCR profile |
| Profile not assigned to org | Assign LCR profile to organization |

**Diagnostic Commands:**

```bash
# Check if routes exist for destination
curl -X POST "https://lcr-service/api/v1/lcr/route" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"destination": "+442012345678", "organizationId": 12345}'

# Check LCR profile
curl "https://lcr-service/api/v1/lcr/profiles?organizationId=12345"

# FreeSWITCH CLI - check LCR lookup
fs_cli -x "lcr 12345 +442012345678"
```

**FreeSWITCH Logs to Check:**

```
grep "lcr_routes" /var/log/freeswitch/freeswitch.log
grep "NO_ROUTE_DESTINATION" /var/log/freeswitch/freeswitch.log
```

---

### 2. Call Fails - USER_BUSY (486/17)

**Symptoms:**
- Call fails with "busy" indication
- SIP 486 Busy Here response
- Q.850 cause code 17

**Possible Causes:**

| Cause | Solution |
|-------|----------|
| Destination actually busy | Retry later or enable voicemail |
| Carrier trunk congestion | Enable failover to secondary carrier |
| DID/trunk capacity exceeded | Increase trunk capacity |
| Incorrect carrier config | Verify carrier gateway settings |

**Diagnostic Steps:**

1. Check if issue is destination-specific or widespread
2. Review carrier channel utilization
3. Check if failover is configured and working
4. Contact carrier if persistent

---

### 3. Call Fails - NORMAL_TEMPORARY_FAILURE (503/41)

**Symptoms:**
- Call fails with temporary failure
- SIP 503 Service Unavailable
- Q.850 cause code 41

**Possible Causes:**

| Cause | Solution |
|-------|----------|
| Carrier gateway down | Check gateway health, enable failover |
| Network connectivity issue | Verify network path to carrier |
| Carrier maintenance | Use backup carrier |
| Gateway overloaded | Reduce traffic or add capacity |

**Diagnostic Commands:**

```bash
# Check gateway health
curl "https://lcr-service/api/v1/lcr/gateways/201/health"

# SIP OPTIONS test
sipsak -s sip:ping@carrier.example.com -vvv

# Network connectivity
traceroute sip.carrier.example.com
```

---

### 4. Call Times Out - NO_ANSWER (480/18)

**Symptoms:**
- Call rings but no answer
- SIP 480 Temporarily Unavailable
- Q.850 cause code 18

**Possible Causes:**

| Cause | Solution |
|-------|----------|
| Destination not answering | Normal behavior |
| Timeout too short | Increase call_timeout value |
| PDD too long | Check carrier PDD, consider alternate route |
| Ring not reaching destination | Contact carrier |

**Configuration Check:**

```xml
<!-- FreeSWITCH timeout settings -->
<action application="set" data="call_timeout=60"/>
<action application="set" data="originate_timeout=120"/>
```

---

### 5. Caller ID Not Displayed Correctly

**Symptoms:**
- Caller ID showing wrong number
- Caller ID showing "Unknown" or "Private"
- Caller name not displaying

**Diagnostic Flow:**

```
┌─────────────────────────────────┐
│ Check requested CLI in request  │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ Is CLI validated for org/user?  │
│              │                  │
│     YES      │       NO         │
│      │       │        │         │
│      ▼       │        ▼         │
│ Continue     │  Using default   │
│              │  CLI             │
└──────────────┴──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ Check carrier CLI support       │
│              │                  │
│  Supported   │  Not supported   │
│      │       │        │         │
│      ▼       │        ▼         │
│ CLI sent     │  CLI stripped    │
│ in INVITE    │  by carrier      │
└──────────────┴──────────────────┘
```

**Verification Commands:**

```bash
# Check allowed CLIs for organization
curl "https://api/v1/organizations/12345/allowed-cli"

# Check user's configured CLI
curl "https://api/v1/users/67890/caller-id"

# FreeSWITCH - check effective CLI
fs_cli -x "uuid_getvar <uuid> effective_caller_id_number"
```

**SIP Header Verification:**

```
# Check these headers in SIP INVITE:
From: <sip:+442012345678@domain>
P-Asserted-Identity: <sip:+442012345678@domain>
Remote-Party-ID: <sip:+442012345678@domain>;party=calling;privacy=off;screen=yes
```

---

### 6. One-Way Audio or No Audio

**Symptoms:**
- Call connects but audio in one direction only
- Call connects with no audio at all
- Audio cutting in and out

**Possible Causes:**

| Cause | Solution |
|-------|----------|
| NAT/firewall blocking RTP | Configure STUN/TURN, check firewall |
| Codec mismatch | Verify codec negotiation |
| Media IP address issue | Check SDP c= line |
| RTP port blocked | Ensure RTP port range open |

**Diagnostic Steps:**

1. Check SDP in INVITE and 200 OK:
```
# Look for:
c=IN IP4 <media_ip>
m=audio <port> RTP/AVP <codecs>
a=rtpmap:...
```

2. Verify RTP traffic:
```bash
# Check for RTP packets
tcpdump -i any port 16384-32768 and host <remote_ip>
```

3. Check codec negotiation:
```bash
fs_cli -x "uuid_getvar <uuid> read_codec"
fs_cli -x "uuid_getvar <uuid> write_codec"
```

**FreeSWITCH RTP Settings:**

```xml
<!-- sofia.conf.xml -->
<param name="ext-rtp-ip" value="$${external_rtp_ip}"/>
<param name="ext-sip-ip" value="$${external_sip_ip}"/>
<param name="rtp-ip" value="$${local_ip_v4}"/>
```

---

### 7. Call Recording Not Working

**Symptoms:**
- Recording file not created
- Recording file empty
- Recording incomplete

**Diagnostic Steps:**

1. Verify recording policy enabled:
```bash
# Check recording flag on call
fs_cli -x "uuid_getvar <uuid> recording_enabled"
```

2. Check recording path:
```bash
# Verify directory exists and writable
ls -la /recordings/${org_id}/
```

3. Check recording process:
```bash
# Check for active recording
fs_cli -x "uuid_getvar <uuid> record_file_name"
```

4. Review logs:
```bash
grep "record_session" /var/log/freeswitch/freeswitch.log
```

---

### 8. Gateway Failover Not Working

**Symptoms:**
- Calls failing despite backup gateways configured
- All calls going to primary gateway only
- Failover not triggering on gateway failure

**Diagnostic Steps:**

1. Verify failover configuration:
```bash
# Check failover causes in dial string
fs_cli -x "uuid_getvar <uuid> failure_causes"
```

2. Check dial string structure:
```
# Correct failover format:
[leg_1=true]sofia/gateway/primary/+441234567|
[leg_2=true]sofia/gateway/secondary/+441234567
```

3. Verify gateway health status:
```bash
curl "https://lcr-service/api/v1/lcr/gateways/201/health"
curl "https://lcr-service/api/v1/lcr/gateways/202/health"
```

4. Check failover threshold settings:
```sql
SELECT * FROM carriers WHERE id = 101;
-- Check: failover_enabled, failover_threshold, failover_window
```

---

### 9. LCR Cache Issues

**Symptoms:**
- Route changes not taking effect
- Old rates being applied
- Disabled routes still being used

**Solution:**

```bash
# Invalidate cache for organization
curl -X POST "https://lcr-service/api/v1/lcr/cache/invalidate" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"organizationId": 12345, "scope": "all"}'

# Check cache status
redis-cli KEYS "lcr:12345:*" | wc -l
```

---

### 10. CDR Not Generated

**Symptoms:**
- Calls completing but no CDR record
- CDR missing fields
- CDR delayed

**Diagnostic Steps:**

1. Check CDR events in FreeSWITCH:
```bash
grep "CHANNEL_DESTROY" /var/log/freeswitch/freeswitch.log | tail -20
```

2. Verify CDR handler:
```bash
fs_cli -x "module_exists mod_cdr_csv"
fs_cli -x "module_exists mod_cdr_mongodb"
```

3. Check CDR database:
```sql
SELECT * FROM call_detail_records 
WHERE uuid = '550e8400-e29b-41d4-a716-446655440000';
```

4. Check CDR processing queue:
```bash
# Check queue depth
rabbitmqctl list_queues | grep cdr
```

---

## Log Locations

| Component | Log Location |
|-----------|--------------|
| FreeSWITCH | `/var/log/freeswitch/freeswitch.log` |
| LCR Service | `/var/log/lcr-service/lcr.log` |
| CDR Service | `/var/log/cdr-service/cdr.log` |
| Recording | `/var/log/recording-service/recording.log` |

---

## Useful FreeSWITCH Commands

```bash
# Show active channels
fs_cli -x "show channels"

# Show channel details
fs_cli -x "uuid_dump <uuid>"

# Show gateway status
fs_cli -x "sofia status gateway <gateway_name>"

# Test LCR lookup
fs_cli -x "lcr <profile> <number>"

# Show SIP registrations
fs_cli -x "sofia status profile external reg"

# Enable SIP trace
fs_cli -x "sofia profile external siptrace on"

# Show call stats
fs_cli -x "show status"
```

---

## Escalation Path

1. **Level 1**: Check logs, verify configuration
2. **Level 2**: Network/SIP trace analysis
3. **Level 3**: Carrier engagement
4. **Level 4**: FreeSWITCH core debugging

---

## Related Documentation

- [Outbound Call Flows](./outbound-call-flows.md)
- [LCR Service API](./lcr-service-api.md)
- [Carrier Integration Guide](../carriers/integration-guide.md)
- [FreeSWITCH Configuration](../freeswitch/configuration.md)
