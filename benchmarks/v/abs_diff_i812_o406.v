module abs_diff_i812_o406(a,b,r);
input [405:0] a,b;
output [405:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
