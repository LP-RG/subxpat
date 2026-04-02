module abs_diff_i680_o340(a,b,r);
input [339:0] a,b;
output [339:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
