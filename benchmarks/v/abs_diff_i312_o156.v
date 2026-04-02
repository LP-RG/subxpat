module abs_diff_i312_o156(a,b,r);
input [155:0] a,b;
output [155:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
