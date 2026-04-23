module abs_diff_i57344_o28672(a,b,r);
input [28671:0] a,b;
output [28671:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
