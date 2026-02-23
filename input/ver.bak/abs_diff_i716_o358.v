module abs_diff_i716_o358(a,b,r);
input [357:0] a,b;
output [357:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
