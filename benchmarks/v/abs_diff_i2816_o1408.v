module abs_diff_i2816_o1408(a,b,r);
input [1407:0] a,b;
output [1407:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
