module abs_diff_i60_o30(a,b,r);
input [29:0] a,b;
output [29:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
