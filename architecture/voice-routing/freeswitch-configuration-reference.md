# FreeSWITCH Configuration Reference

> **Last Updated**: 2026-01-20
> **Related**: [FreeSWITCH Architecture](./freeswitch-architecture.md)

This document provides detailed configuration file examples and parameter references for FreeSWITCH deployment.

## Table of Contents

1. [Configuration File Details](#configuration-file-details)
2. [SIP Profile Parameters](#sip-profile-parameters)
3. [Event Socket Parameters](#event-socket-parameters)
4. [XML CURL Parameters](#xml-curl-parameters)
5. [Conference Profile Parameters](#conference-profile-parameters)
6. [UniMRCP Parameters](#unimrcp-parameters)
7. [ACL Configuration](#acl-configuration)

---

## Configuration File Details

### modules.conf.xml - Complete Reference

```xml
<configuration name="modules.conf" description="Modules">
  <modules>
    <!-- ============================================ -->
    <!-- LOGGERS - Load first for error visibility   -->
    <!-- ============================================ -->
    <load module="mod_console"/>
    <!-- <load module="mod_logfile"/> -->
    <load module="mod_syslog"/>

    <!-- ============================================ -->
    <!-- XML INTERFACES                              -->
    <!-- ============================================ -->
    <!-- <load module="mod_xml_rpc"/> -->
    <load module="mod_xml_curl"/>
    <load module="mod_xml_cdr"/>

    <!-- ============================================ -->
    <!-- EVENT HANDLERS                              -->
    <!-- ============================================ -->
    <!--<load module="mod_cdr_csv"/>-->
    <!-- <load module="mod_event_multicast"/> -->
    <load module="mod_event_socket"/>
    <!-- <load module="mod_zeroconf"/> -->
    <!--<load module="mod_snmp"/>-->

    <!-- ============================================ -->
    <!-- DIRECTORY INTERFACES                        -->
    <!-- ============================================ -->
    <!-- <load module="mod_ldap"/> -->

    <!-- ============================================ -->
    <!-- ENDPOINTS                                   -->
    <!-- ============================================ -->
    <!-- <load module="mod_dingaling"/> -->
    <!-- <load module="mod_iax"/> -->
    <!-- <load module="mod_portaudio"/> -->
    <!-- <load module="mod_alsa"/> -->
    <load module="mod_sofia"/>
    <load module="mod_loopback"/>
    <!-- <load module="mod_woomera"/> -->
    <!-- <load module="mod_openzap"/> -->
    <!-- <load module="mod_unicall"/> -->

    <!-- ============================================ -->
    <!-- APPLICATIONS                                -->
    <!-- ============================================ -->
    <load module="mod_commands"/>
    <load module="mod_conference"/>
    <load module="mod_dptools"/>
    <load module="mod_expr"/>
    <load module="mod_fifo"/>
    <!--<load module="mod_voicemail"/>-->
    <!--<load module="mod_fax"/>-->
    <!--<load module="mod_lcr"/>-->
    <!--<load module="mod_limit"/>-->
    <!--<load module="mod_db"/>-->
    <load module="mod_hash"/>
    <load module="mod_spandsp"/>
    <load module="mod_soundtouch"/>
    <load module="mod_valet_parking"/>
    <!--<load module="mod_curl"/>-->
    <load module="mod_distributor"/>
    <!--<load module="mod_esf"/>-->
    <!--<load module="mod_fsv"/>-->
    <!--<load module="mod_cluechoo"/>-->
    <!--<load module="mod_spy"/>-->

    <!-- ============================================ -->
    <!-- DIALPLAN INTERFACES                         -->
    <!-- ============================================ -->
    <!-- <load module="mod_dialplan_directory"/> -->
    <load module="mod_dialplan_xml"/>
    <!--<load module="mod_dialplan_asterisk"/> -->

    <!-- ============================================ -->
    <!-- CODECS                                      -->
    <!-- ============================================ -->
    <!--<load module="mod_voipcodecs"/>-->
    <!--<load module="mod_g723_1"/>-->
    <!--<load module="mod_g729"/>-->
    <!--<load module="mod_amr"/>-->
    <load module="mod_opencore_amr"/>
    <!--<load module="mod_ilbc"/>-->
    <!--<load module="mod_speex"/>-->
    <!--<load module="mod_h26x"/>-->
    <!--<load module="mod_siren"/>-->
    <!--<load module="mod_celt"/>-->

    <!-- ============================================ -->
    <!-- FILE FORMATS                                -->
    <!-- ============================================ -->
    <load module="mod_sndfile"/>
    <load module="mod_native_file"/>
    <!-- For icecast/mp3 streams/files -->
    <load module="mod_shout"/>
    <!-- For local streams (play all files in directory) -->
    <load module="mod_local_stream"/>
    <load module="mod_tone_stream"/>
    <!--<load module="mod_file_string"/>-->

    <!-- ============================================ -->
    <!-- SCRIPTING LANGUAGES                         -->
    <!-- ============================================ -->
    <load module="mod_spidermonkey"/>
    <!-- <load module="mod_perl"/> -->
    <!-- <load module="mod_python"/> -->
    <!-- <load module="mod_java"/> -->
    <load module="mod_lua"/>

    <!-- ============================================ -->
    <!-- ASR / TTS                                   -->
    <!-- ============================================ -->
    <!-- <load module="mod_flite"/> -->
    <!-- <load module="mod_pocketsphinx"/> -->
    <!-- <load module="mod_cepstral"/> -->
    <!-- <load module="mod_rss"/> -->
    <load module="mod_unimrcp"/>
    
    <!-- ============================================ -->
    <!-- SAY MODULES                                 -->
    <!-- ============================================ -->
    <load module="mod_say_en"/>
    <!-- <load module="mod_say_ru"/> -->
    <!-- <load module="mod_say_zh"/> -->

    <!-- ============================================ -->
    <!-- RED MATTER CUSTOM MODULES                   -->
    <!-- ============================================ -->
    <load module="mod_rmapi"/>
    <load module="mod_rmlogactivity"/>
    <load module="mod_rmvoicemail"/>
    <!--<load module="mod_rmremoterec"/>-->
  </modules>
</configuration>
```

---

### switch.conf.xml - Core Configuration

```xml
<configuration name="switch.conf" description="Core Configuration">

  <cli-keybindings>
    <key name="1" value="help"/>
    <key name="2" value="status"/>
    <key name="3" value="show channels"/>
    <key name="4" value="show calls"/>
    <key name="5" value="sofia status"/>
    <key name="6" value="reloadxml"/>
    <key name="7" value="console loglevel 0"/>
    <key name="8" value="console loglevel 7"/>
    <key name="9" value="sofia status profile internal"/>
    <key name="10" value="sofia profile internal siptrace on"/>
    <key name="11" value="sofia profile internal siptrace off"/>
    <key name="12" value="version"/>
  </cli-keybindings> 
  
  <settings>
    <!-- Colorize the Console -->
    <param name="colorize-console" value="true"/>
    
    <!-- Most channels to allow at once -->
    <param name="max-sessions" value="1500"/>
    
    <!-- Most channels to create per second -->
    <param name="sessions-per-second" value="128"/>
    
    <!-- Default Global Log Level -->
    <!-- Values: debug, info, notice, warning, err, crit, alert -->
    <param name="loglevel" value="debug"/>
    
    <!-- Try to catch recoverable crashes -->
    <param name="crash-protection" value="false"/>
    
    <!-- DTMF Duration Settings -->
    <!--<param name="max_dtmf_duration" value="192000"/>-->
    <!--<param name="default_dtmf_duration" value="8000"/>-->
    
    <!-- Mailer Configuration -->
    <param name="mailer-app" value="/usr/sbin/sendmail"/>
    <param name="mailer-app-args" value="-t -fnoreply@redmatter.com"/>
    
    <!-- Core Dump Configuration -->
    <param name="dump-cores" value="yes"/>
    
    <!-- RTP Port Range -->
    <!--<param name="rtp-start-port" value="16384"/>-->
    <!--<param name="rtp-end-port" value="32768"/>-->
    
    <!-- Enable ZRTP for secure RTP -->
    <param name="rtp-enable-zrtp" value="true"/>

    <!-- Use system time instead of monotonic -->
    <param name="enable-use-system-time" value="true"/>
  </settings>

</configuration>
```

---

## SIP Profile Parameters

### Internal Profile - Complete Parameters

```xml
<profile name="internal1">
  <domains>
    <domain name="all" alias="true" parse="true"/>
  </domains>
  
  <settings>
    <!-- ========================================== -->
    <!-- NETWORK BINDINGS                          -->
    <!-- ========================================== -->
    <param name="sip-ip" value="$${local_ip_v4}"/>
    <param name="sip-port" value="5061"/>
    <param name="rtp-ip" value="$${local_ip_v4}"/>
    <param name="ext-rtp-ip" value="$${external_rtp_ip}"/>
    <param name="ext-sip-ip" value="$${external_sip_ip}"/>
    
    <!-- ========================================== -->
    <!-- CALL PROCESSING                           -->
    <!-- ========================================== -->
    <param name="context" value="default"/>
    <param name="dialplan" value="XML"/>
    <param name="dtmf-duration" value="2000"/>
    <param name="inbound-codec-prefs" value="$${global_codec_prefs}"/>
    <param name="outbound-codec-prefs" value="$${outbound_codec_prefs}"/>
    <param name="hold-music" value="$${hold_music}"/>
    
    <!-- ========================================== -->
    <!-- NAT HANDLING                              -->
    <!-- ========================================== -->
    <param name="apply-nat-acl" value="nat.auto"/>
    <param name="aggressive-nat-detection" value="true"/>
    <param name="local-network-acl" value="localnet.auto"/>
    <param name="NDLB-received-in-nat-reg-contact" value="true"/>
    <param name="NDLB-force-rport" value="true"/>
    <param name="NDLB-broken-auth-hash" value="true"/>
    
    <!-- ========================================== -->
    <!-- SECURITY & AUTHENTICATION                 -->
    <!-- ========================================== -->
    <param name="apply-inbound-acl" value="domains"/>
    <param name="auth-calls" value="true"/>
    <param name="challenge-realm" value="auto_from"/>
    <param name="auth-all-packets" value="false"/>
    
    <!-- ========================================== -->
    <!-- TLS CONFIGURATION                         -->
    <!-- ========================================== -->
    <param name="tls" value="$${internal_ssl_enable}"/>
    <param name="tls-bind-params" value="transport=tls"/>
    <param name="tls-sip-port" value="5071"/>
    <param name="tls-cert-dir" value="$${internal_ssl_dir}"/>
    <param name="tls-version" value="$${sip_tls_version}"/>
    <param name="tls-only" value="false"/>
    <param name="tls-verify-date" value="true"/>
    <param name="tls-verify-depth" value="2"/>
    <param name="tls-verify-in-subjects" value=""/>
    
    <!-- ========================================== -->
    <!-- RTP / MEDIA                               -->
    <!-- ========================================== -->
    <param name="rtp-timeout-sec" value="300"/>
    <param name="rtp-hold-timeout-sec" value="1800"/>
    <param name="enable-timer" value="false"/>
    <param name="session-timeout" value="1800"/>
    <param name="minimum-session-expires" value="120"/>
    <param name="rtp-rewrite-timestamps" value="true"/>
    <param name="pass-rfc2833" value="false"/>
    
    <!-- ========================================== -->
    <!-- RECORDING                                 -->
    <!-- ========================================== -->
    <param name="record-path" value="$${recordings_dir}"/>
    <param name="record-template" value="${caller_id_number}.${target_domain}.${strftime(%Y-%m-%d-%H-%M-%S)}.wav"/>
    
    <!-- ========================================== -->
    <!-- PRESENCE / MESSAGING                      -->
    <!-- ========================================== -->
    <param name="manage-presence" value="true"/>
    <param name="presence-hosts" value="$${domain},$${local_ip_v4}"/>
    <param name="presence-privacy" value="false"/>
    <param name="send-message-query-on-register" value="true"/>
    <param name="send-presence-on-register" value="true"/>
    
    <!-- ========================================== -->
    <!-- REGISTRATION                              -->
    <!-- ========================================== -->
    <param name="inbound-reg-force-matching-username" value="true"/>
    <param name="force-register-domain" value="$${domain}"/>
    <param name="force-subscription-domain" value="$${domain}"/>
    <param name="force-register-db-domain" value="$${domain}"/>
    <param name="log-auth-failures" value="true"/>
    <param name="forward-unsolicited-mwi-notify" value="false"/>
    
    <!-- ========================================== -->
    <!-- WEBRTC SUPPORT                            -->
    <!-- ========================================== -->
    <param name="apply-candidate-acl" value="rfc1918.auto"/>
    <param name="enable-3pcc" value="proxy"/>
    <param name="enable-3pcc-proxy" value="true"/>
    
    <!-- ========================================== -->
    <!-- SIP OPTIONS                               -->
    <!-- ========================================== -->
    <param name="user-agent-string" value="RedMatter-FreeSWITCH"/>
    <param name="debug" value="0"/>
    <param name="sip-trace" value="no"/>
    <param name="log-level" value="0"/>
    <param name="shutdown-on-fail" value="true"/>
  </settings>
  
  <gateways>
    <!-- Gateways loaded dynamically via XML CURL -->
    <X-PRE-PROCESS cmd="include" data="internal/*.xml"/>
  </gateways>
</profile>
```

### External Profile - Complete Parameters

```xml
<profile name="external1">
  <settings>
    <!-- ========================================== -->
    <!-- NETWORK BINDINGS                          -->
    <!-- ========================================== -->
    <param name="sip-ip" value="$${local_ip_v4}"/>
    <param name="sip-port" value="5060"/>
    <param name="rtp-ip" value="$${local_ip_v4}"/>
    <param name="ext-rtp-ip" value="$${external_rtp_ip}"/>
    <param name="ext-sip-ip" value="$${external_sip_ip}"/>
    
    <!-- ========================================== -->
    <!-- CALL PROCESSING                           -->
    <!-- ========================================== -->
    <param name="context" value="public"/>
    <param name="dialplan" value="XML"/>
    <param name="inbound-codec-prefs" value="$${global_codec_prefs}"/>
    <param name="outbound-codec-prefs" value="$${outbound_codec_prefs}"/>
    
    <!-- ========================================== -->
    <!-- SECURITY - Carrier trust model            -->
    <!-- ========================================== -->
    <param name="auth-calls" value="false"/>
    <param name="apply-inbound-acl" value="carriers"/>
    
    <!-- ========================================== -->
    <!-- NAT HANDLING                              -->
    <!-- ========================================== -->
    <param name="aggressive-nat-detection" value="true"/>
    <param name="NDLB-force-rport" value="true"/>
    <param name="NDLB-broken-auth-hash" value="true"/>
    
    <!-- ========================================== -->
    <!-- RTP / MEDIA                               -->
    <!-- ========================================== -->
    <param name="rtp-timeout-sec" value="300"/>
    <param name="rtp-hold-timeout-sec" value="1800"/>
    
    <!-- ========================================== -->
    <!-- CALLER ID HANDLING                        -->
    <!-- ========================================== -->
    <param name="caller-id-in-from" value="true"/>
    <param name="inbound-late-negotiation" value="true"/>
    
    <!-- ========================================== -->
    <!-- REGISTRATION / PRESENCE                   -->
    <!-- ========================================== -->
    <param name="disable-register" value="true"/>
    <param name="manage-presence" value="false"/>
    
    <!-- ========================================== -->
    <!-- SIP OPTIONS                               -->
    <!-- ========================================== -->
    <param name="user-agent-string" value="RedMatter-FreeSWITCH"/>
    <param name="debug" value="0"/>
    <param name="sip-trace" value="no"/>
  </settings>
  
  <gateways>
    <!-- Carrier gateways loaded dynamically -->
    <X-PRE-PROCESS cmd="include" data="external/*.xml"/>
  </gateways>
</profile>
```

### SIP Profile Parameter Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sip-ip` | IP Address | - | IP to bind SIP socket |
| `sip-port` | Integer | 5060 | SIP listening port |
| `rtp-ip` | IP Address | - | IP for RTP media |
| `ext-rtp-ip` | IP Address | - | External RTP IP for NAT |
| `ext-sip-ip` | IP Address | - | External SIP IP for NAT |
| `context` | String | default | Dialplan context for calls |
| `dialplan` | String | XML | Dialplan type |
| `auth-calls` | Boolean | true | Require authentication |
| `apply-inbound-acl` | String | - | ACL for inbound connections |
| `tls` | Boolean | false | Enable TLS |
| `tls-sip-port` | Integer | 5061 | TLS listening port |
| `rtp-timeout-sec` | Integer | 300 | RTP timeout in seconds |
| `manage-presence` | Boolean | true | Handle presence subscriptions |

---

## Event Socket Parameters

### event_socket.conf.xml

```xml
<configuration name="event_socket.conf" description="Socket Client">
  <settings>
    <!-- Disable NAT mapping for ESL -->
    <param name="nat-map" value="false"/>
    
    <!-- Listen on all interfaces -->
    <param name="listen-ip" value="0.0.0.0"/>
    
    <!-- Default ESL port -->
    <param name="listen-port" value="8021"/>
    
    <!-- Authentication password -->
    <param name="password" value="ClueCon"/>
    
    <!-- ACL for socket connections -->
    <param name="apply-inbound-acl" value="socketacl"/>
    
    <!-- Stop accepting new connections when FreeSWITCH is shutting down -->
    <param name="stop-on-bind-error" value="true"/>
  </settings>
</configuration>
```

### ESL Parameter Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `nat-map` | Boolean | false | Enable NAT mapping |
| `listen-ip` | IP Address | 127.0.0.1 | IP to bind ESL socket |
| `listen-port` | Integer | 8021 | ESL listening port |
| `password` | String | ClueCon | Authentication password |
| `apply-inbound-acl` | String | - | ACL for connections |
| `stop-on-bind-error` | Boolean | true | Stop if bind fails |

---

## XML CURL Parameters

### xml_curl.conf.xml

```xml
<configuration name="xml_curl.conf" description="cURL XML Gateway">
  <bindings>
    <!-- Configuration Section Binding -->
    <binding name="configuration">
      <param name="gateway-url" 
             value="http://${CORE_API_HOST}:8080/freeswitch/configuration.xml" 
             bindings="configuration"/>
      <param name="method" value="POST"/>
      <param name="timeout" value="10"/>
      <param name="connect-timeout" value="5"/>
      <param name="disable-100-continue" value="true"/>
      <param name="enable-post-var" value="hostname,section,tag_name,key_name,key_value"/>
    </binding>
    
    <!-- Dialplan Section Binding -->
    <binding name="dialplan">
      <param name="gateway-url" 
             value="http://${CORE_API_HOST}:8080/freeswitch/dialplan.xml" 
             bindings="dialplan"/>
      <param name="method" value="POST"/>
      <param name="timeout" value="10"/>
      <param name="connect-timeout" value="5"/>
    </binding>
    
    <!-- Directory Section Binding -->
    <binding name="directory">
      <param name="gateway-url" 
             value="http://${CORE_API_HOST}:8080/freeswitch/directory.xml" 
             bindings="directory"/>
      <param name="method" value="POST"/>
      <param name="timeout" value="10"/>
      <param name="connect-timeout" value="5"/>
    </binding>
  </bindings>
</configuration>
```

### XML CURL Parameter Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gateway-url` | URL | - | HTTP endpoint URL |
| `bindings` | String | - | Section to bind (configuration/dialplan/directory) |
| `method` | String | POST | HTTP method (GET/POST) |
| `timeout` | Integer | 60 | Request timeout in seconds |
| `connect-timeout` | Integer | 300 | Connection timeout in seconds |
| `disable-100-continue` | Boolean | false | Disable HTTP 100 Continue |
| `enable-post-var` | String | - | Variables to include in POST |

---

## Conference Profile Parameters

### conference.conf.xml - Default Profile

```xml
<profile name="default">
  <!-- Domain for conference names -->
  <param name="domain" value="$${domain}"/>
  
  <!-- Audio Sample Rate -->
  <param name="rate" value="8000"/>
  
  <!-- Audio Interval (ms) -->
  <param name="interval" value="20"/>
  
  <!-- Voice Activity Detection Energy Level -->
  <param name="energy-level" value="300"/>
  
  <!-- Sound File Prefix -->
  <param name="sound-prefix" value="$${sounds_dir}/en/us/callie"/>
  
  <!-- ========================================== -->
  <!-- ENTRY / EXIT SOUNDS                       -->
  <!-- ========================================== -->
  <param name="enter-sound" value="tone_stream://%(200,0,500,600,700)"/>
  <param name="exit-sound" value="tone_stream://%(500,0,300,200,100,50,25)"/>
  <param name="muted-sound" value="conference/conf-muted.wav"/>
  <param name="unmuted-sound" value="conference/conf-unmuted.wav"/>
  <param name="alone-sound" value="conference/conf-alone.wav"/>
  <param name="locked-sound" value="conference/conf-locked.wav"/>
  <param name="max-members-sound" value="conference/conf-full.wav"/>
  <param name="kicked-sound" value="conference/conf-kicked.wav"/>
  <param name="is-locked-sound" value="conference/conf-locked.wav"/>
  <param name="is-unlocked-sound" value="conference/conf-unlocked.wav"/>
  <param name="pin-sound" value="conference/conf-pin.wav"/>
  <param name="bad-pin-sound" value="conference/conf-bad-pin.wav"/>
  
  <!-- ========================================== -->
  <!-- RECORDING                                 -->
  <!-- ========================================== -->
  <param name="auto-record" value="$${recordings_dir}/${conference_name}_${strftime(%Y-%m-%d-%H-%M-%S)}.wav"/>
  
  <!-- ========================================== -->
  <!-- LIMITS                                    -->
  <!-- ========================================== -->
  <param name="max-members" value="100"/>
  <param name="max-members-sound" value="conference/conf-full.wav"/>
  
  <!-- ========================================== -->
  <!-- AUDIO OPTIONS                             -->
  <!-- ========================================== -->
  <param name="comfort-noise" value="true"/>
  <param name="comfort-noise-level" value="1400"/>
  <param name="auto-gain-level" value="true"/>
  <param name="suppress-events" value="start-talking,stop-talking"/>
  
  <!-- ========================================== -->
  <!-- CALLER CONTROLS                           -->
  <!-- ========================================== -->
  <param name="caller-controls" value="default"/>
  <param name="moderator-controls" value="moderator"/>
  
  <!-- ========================================== -->
  <!-- SECURITY                                  -->
  <!-- ========================================== -->
  <!-- <param name="pin" value="1234"/> -->
  <!-- <param name="moderator-pin" value="5678"/> -->
  
  <!-- ========================================== -->
  <!-- MEMBER FLAGS                              -->
  <!-- ========================================== -->
  <param name="moh-sound" value="$${hold_music}"/>
  <param name="member-flags" value="nomoh"/>
</profile>
```

### Conference Parameter Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rate` | Integer | 8000 | Audio sample rate (8000/16000/32000/48000) |
| `interval` | Integer | 20 | Audio frame interval in ms |
| `energy-level` | Integer | 300 | VAD energy threshold |
| `max-members` | Integer | 0 (unlimited) | Maximum conference participants |
| `pin` | String | - | Conference PIN |
| `moderator-pin` | String | - | Moderator PIN |
| `auto-record` | Path | - | Auto-recording file path template |
| `comfort-noise` | Boolean | false | Generate comfort noise |
| `caller-controls` | String | - | Control group for participants |
| `moderator-controls` | String | - | Control group for moderators |

---

## UniMRCP Parameters

### unimrcp.conf.xml

```xml
<configuration name="unimrcp.conf" description="UniMRCP Client">
  <settings>
    <!-- Default profile for speech synthesis -->
    <param name="default-synth-profile" value="speechserver"/>
    
    <!-- Default profile for speech recognition -->
    <param name="default-recog-profile" value="speechserver"/>
    
    <!-- Log level: EMERGENCY|ALERT|CRITICAL|ERROR|WARNING|INFO|DEBUG -->
    <param name="log-level" value="WARNING"/>
    
    <!-- Enable audio streaming -->
    <param name="enable-response-logging" value="false"/>
  </settings>
  
  <profiles>
    <profile name="speechserver">
      <!-- ========================================== -->
      <!-- MRCP SERVER CONNECTION                    -->
      <!-- ========================================== -->
      <param name="server-ip" value="${MRCP_SERVER_IP}"/>
      <param name="server-port" value="5060"/>
      <param name="server-username" value=""/>
      <param name="force-destination" value="false"/>
      
      <!-- ========================================== -->
      <!-- SIP SIGNALING                             -->
      <!-- ========================================== -->
      <param name="sip-transport" value="udp"/>
      <param name="ua-name" value="FreeSWITCH"/>
      <param name="sdp-origin" value="FreeSWITCH"/>
      
      <!-- ========================================== -->
      <!-- RTP MEDIA                                 -->
      <!-- ========================================== -->
      <param name="rtp-ip" value="$${local_ip_v4}"/>
      <param name="rtp-port-min" value="4000"/>
      <param name="rtp-port-max" value="5000"/>
      <param name="playout-delay" value="50"/>
      <param name="max-playout-delay" value="200"/>
      <param name="codecs" value="PCMU PCMA L16/96/8000"/>
      
      <!-- ========================================== -->
      <!-- TIMEOUTS                                  -->
      <!-- ========================================== -->
      <param name="rtcp" value="false"/>
      <param name="rtcp-bye" value="false"/>
      
      <!-- ========================================== -->
      <!-- SYNTH/RECOG DEFAULTS                      -->
      <!-- ========================================== -->
      <param name="speechsynth" value="speechsynth"/>
      <param name="speechrecog" value="speechrecog"/>
    </profile>
  </profiles>
</configuration>
```

### UniMRCP Parameter Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `server-ip` | IP Address | - | MRCP server address |
| `server-port` | Integer | 5060 | MRCP server SIP port |
| `rtp-ip` | IP Address | - | Local RTP IP |
| `rtp-port-min` | Integer | 4000 | RTP port range start |
| `rtp-port-max` | Integer | 5000 | RTP port range end |
| `codecs` | String | - | Supported codecs |
| `playout-delay` | Integer | 50 | Playout delay in ms |

---

## ACL Configuration

### acl.conf.xml

```xml
<configuration name="acl.conf" description="Network Lists">
  <network-lists>
    <!-- Local Network ACL -->
    <list name="localnet.auto" default="deny">
      <node type="allow" cidr="10.0.0.0/8"/>
      <node type="allow" cidr="172.16.0.0/12"/>
      <node type="allow" cidr="192.168.0.0/16"/>
      <node type="allow" cidr="127.0.0.0/8"/>
    </list>
    
    <!-- NAT Auto-detection ACL -->
    <list name="nat.auto" default="allow">
      <node type="deny" cidr="10.0.0.0/8"/>
      <node type="deny" cidr="172.16.0.0/12"/>
      <node type="deny" cidr="192.168.0.0/16"/>
    </list>
    
    <!-- RFC 1918 ACL -->
    <list name="rfc1918.auto" default="allow">
      <node type="allow" cidr="10.0.0.0/8"/>
      <node type="allow" cidr="172.16.0.0/12"/>
      <node type="allow" cidr="192.168.0.0/16"/>
    </list>
    
    <!-- Event Socket ACL -->
    <list name="socketacl" default="deny">
      <node type="allow" cidr="127.0.0.1/32"/>
      <node type="allow" cidr="10.0.0.0/8"/>
      <node type="allow" cidr="172.16.0.0/12"/>
      <node type="allow" cidr="192.168.0.0/16"/>
    </list>
    
    <!-- Domain Registration ACL -->
    <list name="domains" default="deny">
      <node type="allow" domain="$${domain}"/>
    </list>
    
    <!-- Carrier ACL -->
    <list name="carriers" default="deny">
      <!-- Carrier IPs loaded dynamically or configured per environment -->
      <X-PRE-PROCESS cmd="include" data="acl_carriers.xml"/>
    </list>
  </network-lists>
</configuration>
```

### ACL Parameter Reference

| ACL Name | Default | Purpose |
|----------|---------|---------|
| `localnet.auto` | deny | Private network ranges |
| `nat.auto` | allow | NAT detection |
| `rfc1918.auto` | allow | RFC 1918 addresses |
| `socketacl` | deny | ESL connections |
| `domains` | deny | Domain-based access |
| `carriers` | deny | Carrier/trunk access |

---

## Related Documentation

- [FreeSWITCH Architecture Overview](./freeswitch-architecture.md)
- [SIP Trunk Configuration Guide](./sip-trunk-configuration.md)
- [Call Routing Rules](./call-routing-rules.md)
