module abs_diff_i612_o306(a,b,r);
input [305:0] a,b;
output [305:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
