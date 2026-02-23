module abs_diff_i388_o194(a,b,r);
input [193:0] a,b;
output [193:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
