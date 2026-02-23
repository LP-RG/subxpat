module abs_diff_i296_o148(a,b,r);
input [147:0] a,b;
output [147:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
