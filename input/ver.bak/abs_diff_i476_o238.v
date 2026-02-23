module abs_diff_i476_o238(a,b,r);
input [237:0] a,b;
output [237:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
