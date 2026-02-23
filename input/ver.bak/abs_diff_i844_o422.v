module abs_diff_i844_o422(a,b,r);
input [421:0] a,b;
output [421:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
